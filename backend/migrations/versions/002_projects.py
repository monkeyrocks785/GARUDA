"""Create projects table.

Revision ID: 002_projects
Revises: 001_initial
Create Date: 2024-01-02 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002_projects"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="created"),
        sa.Column("current_stage", sa.String(100), nullable=True),
        sa.Column("current_task", sa.String(255), nullable=True),
        sa.Column("progress", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("area_of_interest", sa.Text, nullable=True),
        sa.Column("coordinate_system", sa.String(50), nullable=True),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("tags", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("favorite", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("archived", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("completed_steps", sa.Text, nullable=True),
        sa.Column("pending_steps", sa.Text, nullable=True),
        sa.Column("last_opened_file", sa.String(500), nullable=True),
        sa.Column("last_viewed_map_position", sa.Text, nullable=True),
        sa.Column("selected_layers", sa.Text, nullable=True),
        sa.Column("dashboard_layout", sa.Text, nullable=True),
        sa.Column("user_notes", sa.Text, nullable=True),
        sa.Column("is_processing", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("last_job_id", sa.String(100), nullable=True),
        sa.Column("last_job_status", sa.String(50), nullable=True),
        sa.Column("project_version", sa.String(20), nullable=False, server_default="1.0.0"),
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
        sa.Column("last_opened_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes for common queries
    op.create_index("ix_projects_name", "projects", ["name"])
    op.create_index("ix_projects_status", "projects", ["status"])
    op.create_index("ix_projects_favorite", "projects", ["favorite"])
    op.create_index("ix_projects_archived", "projects", ["archived"])
    op.create_index("ix_projects_created_at", "projects", ["created_at"])
    op.create_index("ix_projects_updated_at", "projects", ["updated_at"])
    op.create_index("ix_projects_last_opened_at", "projects", ["last_opened_at"])


def downgrade() -> None:
    op.drop_index("ix_projects_last_opened_at")
    op.drop_index("ix_projects_updated_at")
    op.drop_index("ix_projects_created_at")
    op.drop_index("ix_projects_archived")
    op.drop_index("ix_projects_favorite")
    op.drop_index("ix_projects_status")
    op.drop_index("ix_projects_name")
    op.drop_table("projects")
