"""Data access helpers for audit log persistence."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db import AuditLog


class AuditRepository:
    """Repository for writing PHI access audit log entries."""

    async def create(
        self,
        session: AsyncSession,
        action: str,
        resource_id: uuid.UUID,
        ip_address: str,
    ) -> AuditLog:
        """Insert an audit log entry and return the persisted instance."""
        entry = AuditLog(
            action=action,
            resource="patient",
            resource_id=resource_id,
            ip_address=ip_address,
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        return entry
