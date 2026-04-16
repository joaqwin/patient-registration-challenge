import logging

import aiosmtplib
from email.mime.text import MIMEText

from src.core.config import settings
from src.models.domain import PatientResponse
from src.notifiers.base import BaseNotifier

logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):
    async def notify(self, patient: PatientResponse) -> None:
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
                password=settings.MAILTRAP_PASS
            )
            logger.info("Confirmation email sent to %s", patient.email)
        except Exception:
            logger.exception("Failed to send confirmation email to %s", patient.email)
