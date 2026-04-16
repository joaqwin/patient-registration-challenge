"""Unit tests for the EmailNotifier and SmsNotifier classes."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from src.core.config import settings
from src.models.domain import PatientResponse
from src.notifiers.email_notifier import EmailNotifier
from src.notifiers.sms_notifier import SmsNotifier


@pytest.fixture
def patient_response() -> PatientResponse:
    """Return a minimal PatientResponse instance for use in notifier tests."""
    return PatientResponse(
        id=uuid.uuid4(),
        name="Jane Doe",
        email="jane@example.com",
        phone="+14155552671",
        document_photo="uploads/doc.jpg",
        created_at=datetime.now(timezone.utc),
    )


async def test_email_notifier_calls_smtp(  # pylint: disable=redefined-outer-name
    patient_response: PatientResponse,
) -> None:
    """EmailNotifier.notify should call aiosmtplib.send with the configured SMTP credentials."""
    with patch(
        "src.notifiers.email_notifier.aiosmtplib.send", new_callable=AsyncMock
    ) as mock_send:
        await EmailNotifier().notify(patient_response)

    mock_send.assert_awaited_once()
    kwargs = mock_send.call_args.kwargs
    assert kwargs["hostname"] == settings.MAILTRAP_HOST
    assert kwargs["port"] == settings.MAILTRAP_PORT
    assert kwargs["username"] == settings.MAILTRAP_USER
    assert kwargs["password"] == settings.MAILTRAP_PASS


async def test_sms_notifier_only_logs(  # pylint: disable=redefined-outer-name
    patient_response: PatientResponse,
) -> None:
    """SmsNotifier.notify should log an info message and perform no external calls."""
    with patch("src.notifiers.sms_notifier.logger") as mock_logger:
        await SmsNotifier().notify(patient_response)

    mock_logger.info.assert_called_once_with(
        "SMS notification not yet implemented for %s", patient_response.email
    )
