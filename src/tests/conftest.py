import os
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from main import app
from src.core.dependencies import get_notifiers, get_session
from src.notifiers.base import BaseNotifier

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://patients_user:patients_pass@localhost:5432/patients_test_db",
)

test_engine = create_async_engine(TEST_DATABASE_URL, future=True, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class _NoOpNotifier(BaseNotifier):
    async def notify(self, patient) -> None:
        pass


def _get_test_notifiers() -> list[BaseNotifier]:
    return [_NoOpNotifier()]


async def _get_test_session() -> AsyncIterator[AsyncSession]:
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture(scope="session")
def apply_migrations() -> None:
    """Run alembic upgrade head against the test database once per test session.
    Not autouse — only pulled in by integration tests via their conftest."""
    from alembic import command
    from alembic.config import Config

    def _run() -> None:
        cfg = Config("alembic.ini")
        cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
        command.upgrade(cfg, "head")

    with ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(_run).result()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_session] = _get_test_session
    app.dependency_overrides[get_notifiers] = _get_test_notifiers
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
