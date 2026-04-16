"""Validator for patient name format."""

import logging
import re

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

_DIGITS_RE = re.compile(r"\d")
# [^\W\d_] matches any unicode letter (word chars minus digits minus underscore).
# Combined with spaces, hyphens, and apostrophes — everything else is rejected.
_VALID_CHARS_RE = re.compile(r"^(?:[^\W\d_]|[\s'\-])+$", re.UNICODE)

MIN_LENGTH = 2
MAX_LENGTH = 100


class NameValidator:  # pylint: disable=too-few-public-methods
    """
    Validates a patient's name.

    Checks performed in order:
        1. Minimum length — at least 2 characters.
        2. Maximum length — at most 100 characters.
        3. No digits      — numbers are not allowed in a name.
        4. Valid chars    — only letters, spaces, hyphens, and apostrophes
                            (supports names like O'Brien or Mary-Jane).
    """

    def validate(self, name: str) -> None:
        """Run all name checks; raises HTTPException on the first failure."""
        self._check_length(name)
        self._check_no_digits(name)
        self._check_valid_chars(name)

    @staticmethod
    def _check_length(name: str) -> None:
        logger.info("Checking name length: %d chars", len(name))
        if len(name) < MIN_LENGTH:
            logger.warning("Name too short: '%s'", name)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Name must be at least {MIN_LENGTH} characters long.",
            )
        if len(name) > MAX_LENGTH:
            logger.warning("Name too long: '%s'", name)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Name must not exceed {MAX_LENGTH} characters.",
            )

    @staticmethod
    def _check_no_digits(name: str) -> None:
        logger.info("Checking name for digits: '%s'", name)
        if _DIGITS_RE.search(name):
            logger.warning("Name contains digits: '%s'", name)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Name must not contain numbers.",
            )

    @staticmethod
    def _check_valid_chars(name: str) -> None:
        logger.info("Checking name for invalid characters: '%s'", name)
        if not _VALID_CHARS_RE.match(name):
            logger.warning("Name contains invalid characters: '%s'", name)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Name may only contain letters, spaces, hyphens, and apostrophes.",
            )
