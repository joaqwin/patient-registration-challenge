import uuid
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.domain import PatientResponse
from src.repositories.patient_repository import PatientRepository

UPLOAD_DIR = Path("uploads")


class PatientService:
    def __init__(self, repo: PatientRepository, notifiers: list | None = None):
        self.repo = repo
        self.notifiers = notifiers if notifiers is not None else []

    async def register(
        self,
        session: AsyncSession,
        name: str,
        email: str,
        phone: str,
        file: UploadFile,
    ) -> PatientResponse:
        existing = await self.repo.get_by_email(session, email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A patient with this email already exists",
            )

        file_path = await self._save_upload(file)

        patient = await self.repo.create(
            session,
            {
                "name": name,
                "email": email,
                "phone": phone,
                "document_photo": str(file_path),
            },
        )
        return PatientResponse.model_validate(patient)

    async def get_all(self, session: AsyncSession) -> list[PatientResponse]:
        patients = await self.repo.get_all(session)
        return [PatientResponse.model_validate(p) for p in patients]

    async def get_by_id(self, session: AsyncSession, id: uuid.UUID) -> PatientResponse:
        patient = await self.repo.get_by_id(session, id)
        if patient is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
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
