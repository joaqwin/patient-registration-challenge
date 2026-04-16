"""Integration test fixtures: migrations and per-test database cleanup."""

import pytest
from sqlalchemy import text

from src.tests.conftest import TEST_SESSION_LOCAL


@pytest.fixture(scope="session", autouse=True)
def _run_migrations(apply_migrations: None) -> None:  # pylint: disable=unused-argument
    """Pull in the session-scoped migration fixture for all integration tests."""


@pytest.fixture(autouse=True)
async def clean_patients() -> None:
    """Delete all patients rows after every integration test."""
    yield
    async with TEST_SESSION_LOCAL() as session:
        await session.execute(text("DELETE FROM patients"))
        await session.commit()
