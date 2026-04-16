"""Unit tests for PatientService business logic."""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import BackgroundTasks, HTTPException

from src.services.patient_service import PatientService


def _orm_patient(**overrides) -> MagicMock:
    attrs = {
        "id": uuid.uuid4(),
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+14155552671",
        "document_photo": "uploads/doc.jpg",
        "created_at": datetime.now(timezone.utc),
    }
    attrs.update(overrides)
    mock = MagicMock()
    for key, val in attrs.items():
        setattr(mock, key, val)
    return mock


@pytest.fixture
def mock_repo() -> AsyncMock:  # pylint: disable=redefined-outer-name
    """Return a mock PatientRepository with a default create() return value."""
    repo = AsyncMock()
    repo.create.return_value = _orm_patient()
    return repo


@pytest.fixture
def mock_notifier() -> AsyncMock:  # pylint: disable=redefined-outer-name
    """Return a mock notifier."""
    return AsyncMock()


@pytest.fixture
def mock_name_validator() -> MagicMock:  # pylint: disable=redefined-outer-name
    """Return a mock NameValidator whose validate() does nothing."""
    v = MagicMock()
    v.validate = MagicMock(return_value=None)
    return v


@pytest.fixture
def mock_email_validator() -> AsyncMock:  # pylint: disable=redefined-outer-name
    """Return a mock EmailValidator whose validate() does nothing."""
    v = AsyncMock()
    v.validate = AsyncMock(return_value=None)
    return v


@pytest.fixture
def mock_phone_validator() -> AsyncMock:  # pylint: disable=redefined-outer-name
    """Return a mock PhoneValidator whose validate() does nothing."""
    v = AsyncMock()
    v.validate = AsyncMock(return_value=None)
    return v


@pytest.fixture
def mock_photo_validator() -> MagicMock:  # pylint: disable=redefined-outer-name
    """Return a mock PhotoValidator whose validate() does nothing."""
    v = MagicMock()
    v.validate = MagicMock(return_value=None)
    return v


@pytest.fixture
def service(request: pytest.FixtureRequest) -> PatientService:  # pylint: disable=redefined-outer-name
    """Return a PatientService wired with all-mock dependencies."""
    _repo = request.getfixturevalue("mock_repo")
    _notifier = request.getfixturevalue("mock_notifier")
    _name_validator = request.getfixturevalue("mock_name_validator")
    _email_validator = request.getfixturevalue("mock_email_validator")
    _phone_validator = request.getfixturevalue("mock_phone_validator")
    _photo_validator = request.getfixturevalue("mock_photo_validator")

    return PatientService(
        repo=_repo,
        notifiers=[_notifier],
        name_validator=_name_validator,
        email_validator=_email_validator,
        phone_validator=_phone_validator,
        photo_validator=_photo_validator,
    )


@pytest.fixture
def mock_upload() -> MagicMock:  # pylint: disable=redefined-outer-name
    """Return a mock UploadFile that yields one chunk then EOF."""
    f = MagicMock()
    f.filename = "doc.jpg"
    f.read = AsyncMock(side_effect=[b"data", b""])
    return f


async def test_register_success(
    service: PatientService,  # pylint: disable=redefined-outer-name
    mock_repo: AsyncMock,  # pylint: disable=redefined-outer-name
    mock_upload: MagicMock,  # pylint: disable=redefined-outer-name
) -> None:
    """register() persists the patient and enqueues exactly one background notification."""
    bg = BackgroundTasks()

    with patch.object(
        PatientService, "_save_upload", new_callable=AsyncMock, return_value=Path("uploads/doc.jpg")
    ):
        result = await service.register(
            session=AsyncMock(),
            name="John Doe",
            email="john@example.com",
            phone="+14155552671",
            file=mock_upload,
            background_tasks=bg,
        )

    assert result.name == "John Doe"
    assert result.email == "john@example.com"
    mock_repo.create.assert_awaited_once()
    assert len(bg.tasks) == 1


async def test_register_duplicate_email(
    service: PatientService,  # pylint: disable=redefined-outer-name
    mock_repo: AsyncMock,  # pylint: disable=redefined-outer-name
    mock_email_validator: AsyncMock,  # pylint: disable=redefined-outer-name
    mock_upload: MagicMock,  # pylint: disable=redefined-outer-name
) -> None:
    """register() raises 409 and never calls repo.create when the email validator rejects."""
    mock_email_validator.validate.side_effect = HTTPException(
        status_code=409,
        detail="The email 'john@example.com' is already registered.",
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.register(
            session=AsyncMock(),
            name="John Doe",
            email="john@example.com",
            phone="+14155552671",
            file=mock_upload,
            background_tasks=BackgroundTasks(),
        )

    assert exc_info.value.status_code == 409
    mock_repo.create.assert_not_awaited()


async def test_get_by_id_not_found(
    service: PatientService,  # pylint: disable=redefined-outer-name
    mock_repo: AsyncMock,  # pylint: disable=redefined-outer-name
) -> None:
    """get_by_id() raises 404 when the repository returns None."""
    mock_repo.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await service.get_by_id(session=AsyncMock(), patient_id=uuid.uuid4())

    assert exc_info.value.status_code == 404
