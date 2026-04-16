"""Validator for patient email address format and uniqueness."""

import logging
import re

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.patient_repository import PatientRepository

logger = logging.getLogger(__name__)

# RFC 5322 simplified — good enough for user input; pydantic's EmailStr uses the same library.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EmailValidator:  # pylint: disable=too-few-public-methods
    """
    Validates a patient's email address.

    Checks performed in order:
        1. Format     — must be a structurally valid e-mail address.
        2. Uniqueness — no other patient may share the same address.
    """

    async def validate(
        self,
        email: str,
        session: AsyncSession,
        repo: PatientRepository,
    ) -> None:
        """Run all email checks; raises HTTPException on the first failure."""
        self._check_format(email)
        await self._check_unique(email, session, repo)

    @staticmethod
    def _check_format(email: str) -> None:
        logger.info("Checking email format: %s", email)
        if not _EMAIL_RE.match(email):
            logger.warning("Invalid email format: %s", email)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Invalid email address. "
                    "Please provide a valid format (e.g. user@example.com)."
                ),
            )

    @staticmethod
    async def _check_unique(
        email: str,
        session: AsyncSession,
        repo: PatientRepository,
    ) -> None:
        logger.info("Checking email uniqueness: %s", email)
        existing = await repo.get_by_email(session, email)
        if existing is not None:
            logger.warning("Email already registered: %s", email)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"The email '{email}' is already registered. "
                    "Please use a different email address."
                ),
            )
