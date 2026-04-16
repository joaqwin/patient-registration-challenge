"""Business logic layer for patient registration and retrieval."""

import logging
import uuid
from pathlib import Path

import aiofiles
from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.domain import PatientDetail, PatientSummary
from src.notifiers.base import BaseNotifier
from src.repositories.patient_repository import PatientRepository
from src.services.encryption_service import EncryptionService
from src.validators.email_validator import EmailValidator
from src.validators.name_validator import NameValidator
from src.validators.phone_validator import PhoneValidator
from src.validators.photo_validator import PhotoValidator

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads")


class PatientService:  # pylint: disable=too-many-instance-attributes
    """Orchestrates validation, persistence, and notification for patient operations."""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        repo: PatientRepository,
        notifiers: list[BaseNotifier],
        encryption_service: EncryptionService | None = None,
        name_validator: NameValidator | None = None,
        email_validator: EmailValidator | None = None,
        phone_validator: PhoneValidator | None = None,
        photo_validator: PhotoValidator | None = None,
    ):
        self.repo = repo
        self.notifiers = notifiers
        self.encryption_service = encryption_service or EncryptionService()
        self.name_validator = name_validator or NameValidator()
        self.email_validator = email_validator or EmailValidator()
        self.phone_validator = phone_validator or PhoneValidator()
        self.photo_validator = photo_validator or PhotoValidator()

    async def register(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        session: AsyncSession,
        name: str,
        email: str,
        phone: str,
        file: UploadFile,
        background_tasks: BackgroundTasks,
    ) -> PatientDetail:
        """Validate, persist, and notify for a new patient registration."""
        logger.info("Validating name for new patient: %s", name)
        self.name_validator.validate(name)

        logger.info("Validating email for new patient: %s", email)
        await self.email_validator.validate(email, session, self.repo)

        logger.info("Validating phone for new patient: %s", phone)
        await self.phone_validator.validate(phone, session, self.repo)

        logger.info("Validating document photo for patient: %s", email)
        self.photo_validator.validate(file)

        logger.info("Saving document photo for patient: %s", email)
        file_path = await self._save_upload(file, self.encryption_service)

        logger.info("Creating patient record in DB: %s", email)
        patient = await self.repo.create(
            session,
            {
                "name": name,
                "email": email,
                "phone": phone,
                "document_photo": str(file_path),
            },
        )

        response = PatientDetail.model_validate(patient)
        logger.info("Patient registered successfully: id=%s email=%s", response.id, response.email)

        for notifier in self.notifiers:
            background_tasks.add_task(notifier.notify, response)

        return response

    async def get_all(self, session: AsyncSession) -> list[PatientSummary]:
        """Return all patients ordered by registration date."""
        logger.info("Fetching all patients from DB")
        patients = await self.repo.get_all(session)
        logger.info("Fetched %d patient(s)", len(patients))
        return [PatientSummary.model_validate(p) for p in patients]

    async def get_by_id(self, session: AsyncSession, patient_id: uuid.UUID) -> PatientDetail:
        """Return a single patient by UUID, or raise 404 if not found."""
        logger.info("Fetching patient from DB: id=%s", patient_id)
        patient = await self.repo.get_by_id(session, patient_id)
        if patient is None:
            logger.warning("Patient not found: id=%s", patient_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found.",
            )
        return PatientDetail.model_validate(patient)

    @staticmethod
    async def _save_upload(file: UploadFile, encryption_service: EncryptionService) -> Path:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        suffix = Path(file.filename or "").suffix
        filename = f"{uuid.uuid4().hex}{suffix}"
        file_path = UPLOAD_DIR / filename

        chunks: list[bytes] = []
        while chunk := await file.read(1024 * 1024):
            chunks.append(chunk)
        plaintext = b"".join(chunks)

        encrypted = encryption_service.encrypt(plaintext)

        async with aiofiles.open(file_path, "wb") as out:
            await out.write(encrypted)

        return file_path
