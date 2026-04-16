"""Data access helpers for patient persistence."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db import Patient


class PatientRepository:
    """Repository wrapper around patient database operations."""

    async def create(self, session: AsyncSession, patient_data: dict[str, Any]) -> Patient:
        """Insert a patient row and return the refreshed ORM instance."""
        patient = Patient(**patient_data)
        session.add(patient)
        await session.commit()
        await session.refresh(patient)
        return patient

    async def get_by_id(self, session: AsyncSession, patient_id: uuid.UUID) -> Patient | None:
        """Return a patient by UUID, or None when no row exists."""
        result = await session.execute(select(Patient).where(Patient.id == patient_id))
        return result.scalar_one_or_none()

    async def get_all(self, session: AsyncSession) -> list[Patient]:
        """Return all patients ordered by newest first."""
        result = await session.execute(select(Patient).order_by(Patient.created_at.desc()))
        return list(result.scalars().all())

    async def get_by_email(self, session: AsyncSession, email: str) -> Patient | None:
        """Return a patient matching the given email address."""
        result = await session.execute(select(Patient).where(Patient.email == email))
        return result.scalar_one_or_none()

    async def get_by_phone(self, session: AsyncSession, phone: str) -> Patient | None:
        """Return a patient matching the given phone number."""
        result = await session.execute(select(Patient).where(Patient.phone == phone))
        return result.scalar_one_or_none()
