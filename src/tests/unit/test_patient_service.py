import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import BackgroundTasks, HTTPException

from src.models.domain import PatientResponse
from src.services.patient_service import PatientService


def _orm_patient(**overrides) -> MagicMock:
    attrs = dict(
        id=uuid.uuid4(),
        name="John Doe",
        email="john@example.com",
        phone="+14155552671",
        document_photo="uploads/doc.jpg",
        created_at=datetime.now(timezone.utc),
    )
    attrs.update(overrides)
    mock = MagicMock()
    for key, val in attrs.items():
        setattr(mock, key, val)
    return mock


@pytest.fixture
def mock_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_email.return_value = None
    repo.create.return_value = _orm_patient()
    return repo


@pytest.fixture
def mock_notifier() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(mock_repo: AsyncMock, mock_notifier: AsyncMock) -> PatientService:
    return PatientService(repo=mock_repo, notifiers=[mock_notifier])


@pytest.fixture
def mock_upload() -> MagicMock:
    f = MagicMock()
    f.filename = "doc.jpg"
    f.read = AsyncMock(side_effect=[b"data", b""])
    return f


async def test_register_success(
    service: PatientService,
    mock_repo: AsyncMock,
    mock_notifier: AsyncMock,
    mock_upload: MagicMock,
) -> None:
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
    assert len(bg.tasks) == 1  # one background task queued per notifier


async def test_register_duplicate_email(
    service: PatientService,
    mock_repo: AsyncMock,
    mock_upload: MagicMock,
) -> None:
    mock_repo.get_by_email.return_value = _orm_patient()

    with pytest.raises(HTTPException) as exc_info:
        await service.register(
            session=AsyncMock(),
            name="John Doe",
            email="john@example.com",
            phone="+14155552671",
            file=mock_upload,
            background_tasks=BackgroundTasks(),
        )

    assert exc_info.value.status_code == 400
    mock_repo.create.assert_not_awaited()


async def test_get_by_id_not_found(
    service: PatientService,
    mock_repo: AsyncMock,
) -> None:
    mock_repo.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await service.get_by_id(session=AsyncMock(), id=uuid.uuid4())

    assert exc_info.value.status_code == 404
