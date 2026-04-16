"""Validator for patient document photo file type."""

import logging
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


class PhotoValidator:  # pylint: disable=too-few-public-methods
    """
    Validates a patient's document photo upload.

    Checks performed in order:
        1. File extension  — must be one of: .jpg, .jpeg, .png, .webp.
        2. Content-Type    — must be a recognised image MIME type.
    """

    def validate(self, file: UploadFile) -> None:
        """Run all photo checks; raises HTTPException on the first failure."""
        self._check_extension(file)
        self._check_content_type(file)

    @staticmethod
    def _check_extension(file: UploadFile) -> None:
        suffix = Path(file.filename or "").suffix.lower()
        logger.info("Checking photo extension: '%s'", suffix)
        if suffix not in ALLOWED_EXTENSIONS:
            logger.warning("Invalid photo extension: '%s'", suffix)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Invalid file extension '{suffix}'. "
                    f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
                ),
            )

    @staticmethod
    def _check_content_type(file: UploadFile) -> None:
        logger.info("Checking photo content type: '%s'", file.content_type)
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            logger.warning("Invalid photo content type: '%s'", file.content_type)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Invalid content type '{file.content_type}'. "
                    f"Allowed types: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}."
                ),
            )
