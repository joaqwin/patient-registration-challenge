from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings
from src.notifiers.base import BaseNotifier
from src.notifiers.email_notifier import EmailNotifier

engine = create_async_engine(settings.DATABASE_URL, future=True)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


def get_notifiers() -> list[BaseNotifier]:
    return [EmailNotifier()]
