"""Initial migration - create health_records table.

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "health_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="healthy"),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("component", sa.String(100), nullable=False, server_default="system"),
        sa.Column(
            "checked_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_health_records_component", "health_records", ["component"])
    op.create_index("ix_health_records_created_at", "health_records", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_health_records_created_at")
    op.drop_index("ix_health_records_component")
    op.drop_table("health_records")
