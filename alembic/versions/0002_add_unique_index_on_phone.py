"""add unique index on phone

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-15

"""
from typing import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_patients_phone", "patients", ["phone"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_patients_phone", table_name="patients")
