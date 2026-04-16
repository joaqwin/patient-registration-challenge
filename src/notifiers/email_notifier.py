"""Email notifier — sends a confirmation email via Mailtrap SMTP."""

import logging
from email.mime.text import MIMEText

import aiosmtplib

from src.core.config import settings
from src.models.domain import PatientResponse
from src.notifiers.base import BaseNotifier

logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):  # pylint: disable=too-few-public-methods
    """Sends a plain-text registration confirmation email through Mailtrap."""

    async def notify(self, patient: PatientResponse) -> None:
        """Send a confirmation email to the newly registered patient."""
        message = MIMEText(
            f"Hi {patient.name},\n\n"
            "Your registration has been confirmed.\n\n"
            f"Name:  {patient.name}\n"
            f"Email: {patient.email}\n\n"
            "Welcome aboard!"
        )
        message["Subject"] = "Registration confirmed"
        message["From"] = settings.MAILTRAP_USER
        message["To"] = patient.email

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.MAILTRAP_HOST,
                port=settings.MAILTRAP_PORT,
                username=settings.MAILTRAP_USER,
                password=settings.MAILTRAP_PASS,
                start_tls=True,
            )
            logger.info("Confirmation email sent to %s", patient.email)
        except (aiosmtplib.SMTPException, OSError):
            logger.exception("Failed to send confirmation email to %s", patient.email)
