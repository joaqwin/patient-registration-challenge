"""Dependency providers for the FastAPI application."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings
from src.notifiers.base import BaseNotifier
from src.notifiers.email_notifier import EmailNotifier

engine = create_async_engine(settings.DATABASE_URL, future=True)

async_session_local = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield a database session for request-scoped dependencies."""
    async with async_session_local() as session:
        yield session


def get_notifiers() -> list[BaseNotifier]:
    """Return the notifiers used after a patient is registered."""
    return [EmailNotifier()]
