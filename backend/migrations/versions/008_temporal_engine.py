"""Add temporal engine tables.

Revision ID: 008_temporal_engine
Revises: 007_mission_engine
Create Date: 2026-07-07
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008_temporal_engine"
down_revision: str | None = "007_mission_engine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "timelines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("group_by", sa.String(50), default="date", index=True),
        sa.Column("sort_order", sa.String(20), default="asc"),
        sa.Column("entry_count", sa.Integer, default=0),
        sa.Column("favorite", sa.Boolean, default=False, index=True),
        sa.Column("archived", sa.Boolean, default=False, index=True),
        sa.Column("tags", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("storage_path", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("modified_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "timeline_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("timeline_id", sa.String(36), sa.ForeignKey("timelines.id", ondelete="CASCADE"), index=True),
        sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id", ondelete="CASCADE"), index=True),
        sa.Column("acquisition_date", sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column("acquisition_time", sa.String(20), nullable=True),
        sa.Column("sensor_name", sa.String(255), nullable=True, index=True),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("resolution", sa.String(100), nullable=True),
        sa.Column("mission_id", sa.String(36), nullable=True, index=True),
        sa.Column("aoi_id", sa.String(36), nullable=True),
        sa.Column("dataset_type", sa.String(50), nullable=True, index=True),
        sa.Column("sort_order", sa.Integer, default=0),
        sa.Column("visibility", sa.Boolean, default=True),
        sa.Column("opacity", sa.Float, default=1.0),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "comparison_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("timeline_id", sa.String(36), sa.ForeignKey("timelines.id", ondelete="CASCADE"), index=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("mode", sa.String(50), default="side_by_side"),
        sa.Column("left_entry_id", sa.String(36), nullable=True),
        sa.Column("right_entry_id", sa.String(36), nullable=True),
        sa.Column("swipe_position", sa.Float, default=50.0),
        sa.Column("opacity", sa.Float, default=1.0),
        sa.Column("linked_pan_zoom", sa.Boolean, default=True),
        sa.Column("map_center_lat", sa.Float, nullable=True),
        sa.Column("map_center_lng", sa.Float, nullable=True),
        sa.Column("map_zoom", sa.Float, nullable=True),
        sa.Column("status", sa.String(50), default="active", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("modified_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "timeline_bookmarks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("timeline_id", sa.String(36), sa.ForeignKey("timelines.id", ondelete="CASCADE"), index=True),
        sa.Column("entry_id", sa.String(36), nullable=True),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("bookmark_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("color", sa.String(20), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "timeline_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("timeline_id", sa.String(36), sa.ForeignKey("timelines.id", ondelete="CASCADE"), index=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("details", sa.Text, nullable=True),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", sa.String(36), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("timeline_logs")
    op.drop_table("timeline_bookmarks")
    op.drop_table("comparison_sessions")
    op.drop_table("timeline_entries")
    op.drop_table("timelines")
