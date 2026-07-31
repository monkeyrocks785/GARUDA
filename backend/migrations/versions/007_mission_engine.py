"""Add mission engine tables.

Revision ID: 007_mission_engine
Revises: 006_pipeline_engine
Create Date: 2026-07-07
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "007_mission_engine"
down_revision: str | None = "006_pipeline_engine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "missions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("code", sa.String(50), nullable=True, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("classification", sa.String(100), nullable=True, index=True),
        sa.Column("status", sa.String(50), default="planning", index=True),
        sa.Column("priority", sa.String(50), default="medium", index=True),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("mission_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mission_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("area_of_interest", sa.Text, nullable=True),
        sa.Column("tags", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("favorite", sa.Boolean, default=False, index=True),
        sa.Column("archived", sa.Boolean, default=False, index=True),
        sa.Column("project_count", sa.Integer, default=0),
        sa.Column("dataset_count", sa.Integer, default=0),
        sa.Column("pipeline_count", sa.Integer, default=0),
        sa.Column("report_count", sa.Integer, default=0),
        sa.Column("storage_path", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("modified_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "mission_projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mission_id", sa.String(36), sa.ForeignKey("missions.id", ondelete="CASCADE"), index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), index=True),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("notes", sa.Text, nullable=True),
    )

    op.create_table(
        "mission_activity",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mission_id", sa.String(36), sa.ForeignKey("missions.id", ondelete="CASCADE"), index=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("details", sa.Text, nullable=True),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", sa.String(36), nullable=True),
        sa.Column("performed_by", sa.String(255), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "mission_notes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mission_id", sa.String(36), sa.ForeignKey("missions.id", ondelete="CASCADE"), index=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("modified_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "mission_tags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mission_id", sa.String(36), sa.ForeignKey("missions.id", ondelete="CASCADE"), index=True),
        sa.Column("tag", sa.String(100), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("mission_tags")
    op.drop_table("mission_notes")
    op.drop_table("mission_activity")
    op.drop_table("mission_projects")
    op.drop_table("missions")
