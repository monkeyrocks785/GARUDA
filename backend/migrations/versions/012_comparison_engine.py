"""Temporal Comparison Engine migration.

Revision ID: 012_comparison_engine
Revises: 011_registration_engine
Create Date: 2025-01-25
"""

import sqlalchemy as sa
from alembic import op

revision = "012_comparison_engine"
down_revision = "011_registration_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # comparison_sessions
    op.create_table(
        "comparison_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("dataset_paths", sa.Text, nullable=False),
        sa.Column("dataset_labels", sa.Text, nullable=True),
        sa.Column("mode", sa.String(50), server_default="side_by_side"),
        sa.Column("difference_type", sa.String(50), nullable=True),
        sa.Column("difference_threshold", sa.Float, nullable=True),
        sa.Column("sync_options", sa.Text, server_default="[]"),
        sa.Column("timeline_position", sa.Integer, nullable=True),
        sa.Column("playback_speed", sa.Float, nullable=True),
        sa.Column("is_playing", sa.Boolean, server_default="0"),
        sa.Column("is_looping", sa.Boolean, server_default="0"),
        sa.Column("layout_state", sa.Text, nullable=True),
        sa.Column("map_state", sa.Text, nullable=True),
        sa.Column("opacity", sa.Float, server_default="1.0"),
        sa.Column("swipe_position", sa.Float, server_default="0.5"),
        sa.Column("blink_interval_ms", sa.Integer, server_default="1000"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("pipeline_id", sa.String(36), nullable=True, index=True),
        sa.Column("favorite", sa.Boolean, server_default="0"),
        sa.Column("archived", sa.Boolean, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("last_opened_at", sa.DateTime, nullable=True),
    )

    # comparison_views
    op.create_table(
        "comparison_views",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("comparison_sessions.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("view_index", sa.Integer, nullable=False),
        sa.Column("dataset_path", sa.Text, nullable=False),
        sa.Column("dataset_label", sa.String(255), nullable=False),
        sa.Column("display_settings", sa.Text, nullable=True),
        sa.Column("visible", sa.Boolean, server_default="1"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # comparison_bookmarks
    op.create_table(
        "comparison_bookmarks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("comparison_sessions.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("timeline_position", sa.Integer, nullable=True),
        sa.Column("map_state", sa.Text, nullable=True),
        sa.Column("opacity", sa.Float, nullable=True),
        sa.Column("swipe_position", sa.Float, nullable=True),
        sa.Column("mode", sa.String(50), nullable=True),
        sa.Column("view_settings", sa.Text, nullable=True),
        sa.Column("sort_order", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # comparison_annotations
    op.create_table(
        "comparison_annotations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("comparison_sessions.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("annotation_type", sa.String(50), nullable=False),
        sa.Column("geometry", sa.Text, nullable=False),
        sa.Column("label", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("color", sa.String(20), server_default="#FF0000"),
        sa.Column("stroke_width", sa.Integer, server_default="2"),
        sa.Column("fill_opacity", sa.Float, server_default="0.3"),
        sa.Column("timeline_position", sa.Integer, nullable=True),
        sa.Column("view_index", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # comparison_exports
    op.create_table(
        "comparison_exports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("comparison_sessions.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("export_format", sa.String(50), nullable=False),
        sa.Column("export_scope", sa.String(50), nullable=False),
        sa.Column("output_path", sa.Text, nullable=False),
        sa.Column("file_size", sa.Integer, nullable=True),
        sa.Column("export_options", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), server_default="completed"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    # comparison_measurements
    op.create_table(
        "comparison_measurements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("comparison_sessions.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("measurement_type", sa.String(50), nullable=False),
        sa.Column("unit", sa.String(20), server_default="pixels"),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("geometry", sa.Text, nullable=False),
        sa.Column("label", sa.String(255), nullable=True),
        sa.Column("timeline_position", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("comparison_measurements")
    op.drop_table("comparison_exports")
    op.drop_table("comparison_annotations")
    op.drop_table("comparison_bookmarks")
    op.drop_table("comparison_views")
    op.drop_table("comparison_sessions")
