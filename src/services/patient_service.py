import logging
import uuid
from pathlib import Path

import aiofiles

logger = logging.getLogger(__name__)
from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.domain import PatientResponse
from src.notifiers.base import BaseNotifier
from src.repositories.patient_repository import PatientRepository
from src.validators.email_validator import EmailValidator
from src.validators.phone_validator import PhoneValidator

UPLOAD_DIR = Path("uploads")


class PatientService:
    def __init__(
        self,
        repo: PatientRepository,
        notifiers: list[BaseNotifier],
        email_validator: EmailValidator | None = None,
        phone_validator: PhoneValidator | None = None,
    ):
        self.repo = repo
        self.notifiers = notifiers
        self.email_validator = email_validator or EmailValidator()
        self.phone_validator = phone_validator or PhoneValidator()

    async def register(
        self,
        session: AsyncSession,
        name: str,
        email: str,
        phone: str,
        file: UploadFile,
        background_tasks: BackgroundTasks,
    ) -> PatientResponse:
        logger.info("Validating email for new patient: %s", email)
        await self.email_validator.validate(email, session, self.repo)

        logger.info("Validating phone for new patient: %s", phone)
        await self.phone_validator.validate(phone, session, self.repo)

        logger.info("Saving document photo for patient: %s", email)
        file_path = await self._save_upload(file)

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

        response = PatientResponse.model_validate(patient)
        logger.info("Patient registered successfully: id=%s email=%s", response.id, response.email)

        for notifier in self.notifiers:
            background_tasks.add_task(notifier.notify, response)

        return response

    async def get_all(self, session: AsyncSession) -> list[PatientResponse]:
        logger.info("Fetching all patients from DB")
        patients = await self.repo.get_all(session)
        logger.info("Fetched %d patient(s)", len(patients))
        return [PatientResponse.model_validate(p) for p in patients]

    async def get_by_id(self, session: AsyncSession, id: uuid.UUID) -> PatientResponse:
        logger.info("Fetching patient from DB: id=%s", id)
        patient = await self.repo.get_by_id(session, id)
        if patient is None:
            logger.warning("Patient not found: id=%s", id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found.",
            )
        return PatientResponse.model_validate(patient)

    @staticmethod
    async def _save_upload(file: UploadFile) -> Path:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        suffix = Path(file.filename or "").suffix
        filename = f"{uuid.uuid4().hex}{suffix}"
        file_path = UPLOAD_DIR / filename
        async with aiofiles.open(file_path, "wb") as out:
            while chunk := await file.read(1024 * 1024):
                await out.write(chunk)
        return file_path
