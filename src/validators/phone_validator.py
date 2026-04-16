"""Validator for patient phone number format and uniqueness."""

import logging
import re

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.patient_repository import PatientRepository

logger = logging.getLogger(__name__)

# +1 followed by exactly 10 digits (NANP format).
_PHONE_RE = re.compile(r"^\+1\d{10}$")


class PhoneValidator:  # pylint: disable=too-few-public-methods
    """
    Validates a patient's phone number.

    Checks performed in order:
        1. Format     — must be +1 followed by exactly 10 digits (e.g. +14155552671).
        2. Uniqueness — no other patient may share the same number.
    """

    async def validate(
        self,
        phone: str,
        session: AsyncSession,
        repo: PatientRepository,
    ) -> None:
        """Run all phone checks; raises HTTPException on the first failure."""
        self._check_format(phone)
        await self._check_unique(phone, session, repo)

    @staticmethod
    def _check_format(phone: str) -> None:
        logger.info("Checking phone format: %s", phone)
        if not _PHONE_RE.match(phone):
            logger.warning("Invalid phone format: %s", phone)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Invalid phone number '{phone}'. "
                    "Phone must start with +1 followed by exactly 10 digits, "
                    "with no spaces (e.g. +14155552671)."
                ),
            )

    @staticmethod
    async def _check_unique(
        phone: str,
        session: AsyncSession,
        repo: PatientRepository,
    ) -> None:
        logger.info("Checking phone uniqueness: %s", phone)
        existing = await repo.get_by_phone(session, phone)
        if existing is not None:
            logger.warning("Phone already registered: %s", phone)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"The phone number '{phone}' is already registered. "
                    "Please use a different number."
                ),
            )
