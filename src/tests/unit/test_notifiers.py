import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from src.core.config import settings
from src.models.domain import PatientResponse
from src.notifiers.email_notifier import EmailNotifier
from src.notifiers.sms_notifier import SmsNotifier


@pytest.fixture
def patient() -> PatientResponse:
    return PatientResponse(
        id=uuid.uuid4(),
        name="Jane Doe",
        email="jane@example.com",
        phone="+14155552671",
        document_photo="uploads/doc.jpg",
        created_at=datetime.now(timezone.utc),
    )


async def test_email_notifier_calls_smtp(patient: PatientResponse) -> None:
    with patch(
        "src.notifiers.email_notifier.aiosmtplib.send", new_callable=AsyncMock
    ) as mock_send:
        await EmailNotifier().notify(patient)

    mock_send.assert_awaited_once()
    kwargs = mock_send.call_args.kwargs
    assert kwargs["hostname"] == settings.MAILTRAP_HOST
    assert kwargs["port"] == settings.MAILTRAP_PORT
    assert kwargs["username"] == settings.MAILTRAP_USER
    assert kwargs["password"] == settings.MAILTRAP_PASS


async def test_sms_notifier_only_logs(patient: PatientResponse) -> None:
    with patch("src.notifiers.sms_notifier.logger") as mock_logger:
        await SmsNotifier().notify(patient)

    mock_logger.info.assert_called_once_with(
        "SMS notification not yet implemented for %s", patient.email
    )
