import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db import Patient


class PatientRepository:
    async def create(self, session: AsyncSession, patient_data: dict[str, Any]) -> Patient:
        patient = Patient(**patient_data)
        session.add(patient)
        await session.commit()
        await session.refresh(patient)
        return patient

    async def get_by_id(self, session: AsyncSession, id: uuid.UUID) -> Patient | None:
        result = await session.execute(select(Patient).where(Patient.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, session: AsyncSession) -> list[Patient]:
        result = await session.execute(select(Patient).order_by(Patient.created_at.desc()))
        return list(result.scalars().all())

    async def get_by_email(self, session: AsyncSession, email: str) -> Patient | None:
        result = await session.execute(select(Patient).where(Patient.email == email))
        return result.scalar_one_or_none()
