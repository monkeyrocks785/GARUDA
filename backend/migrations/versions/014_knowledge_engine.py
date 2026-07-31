"""014 - Knowledge Engine

Revision ID: 014_knowledge_engine
Revises: 013_intelligence_engine
Create Date: 2026-07-08
"""

import sqlalchemy as sa
from alembic import op

revision = "014_knowledge_engine"
down_revision = "013_intelligence_engine"


def upgrade() -> None:
    # ── entities ──────────────────────────────────────────────────────────
    op.create_table(
        "entities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "project_id", sa.String(36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"), index=True,
        ),
        sa.Column("entity_type", sa.String(50), index=True),
        sa.Column("name", sa.String(255)),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(50), server_default="active", index=True),
        sa.Column("confidence", sa.Float, server_default=sa.text("1.0")),
        sa.Column("geometry_json", sa.Text, nullable=True),
        sa.Column("bbox_min_x", sa.Float, nullable=True),
        sa.Column("bbox_min_y", sa.Float, nullable=True),
        sa.Column("bbox_max_x", sa.Float, nullable=True),
        sa.Column("bbox_max_y", sa.Float, nullable=True),
        sa.Column("centroid_x", sa.Float, nullable=True),
        sa.Column("centroid_y", sa.Float, nullable=True),
        sa.Column("attributes_json", sa.Text, nullable=True),
        sa.Column("tags_json", sa.Text, nullable=True),
        sa.Column("analyst_notes", sa.Text, nullable=True),
        sa.Column("observation_count", sa.Integer, server_default=sa.text("0")),
        sa.Column("first_observed_at", sa.DateTime, nullable=True),
        sa.Column("last_observed_at", sa.DateTime, nullable=True),
        sa.Column("favorite", sa.Boolean, server_default=sa.text("0")),
        sa.Column("archived", sa.Boolean, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "modified_at", sa.DateTime,
            server_default=sa.func.now(), onupdate=sa.func.now(),
        ),
    )

    # ── entity_observations ───────────────────────────────────────────────
    op.create_table(
        "entity_observations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "entity_id", sa.String(36),
            sa.ForeignKey("entities.id", ondelete="CASCADE"), index=True,
        ),
        sa.Column("observation_type", sa.String(50)),
        sa.Column("source_id", sa.String(36), nullable=True, index=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("confidence", sa.Float, server_default=sa.text("1.0")),
        sa.Column("geometry_json", sa.Text, nullable=True),
        sa.Column("attributes_json", sa.Text, nullable=True),
        sa.Column("observed_at", sa.DateTime, nullable=True),
        sa.Column("analyst_notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── entity_events ─────────────────────────────────────────────────────
    op.create_table(
        "entity_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "entity_id", sa.String(36),
            sa.ForeignKey("entities.id", ondelete="CASCADE"), index=True,
        ),
        sa.Column("event_type", sa.String(50), index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("attributes_json", sa.Text, nullable=True),
        sa.Column("geometry_json", sa.Text, nullable=True),
        sa.Column("confidence", sa.Float, server_default=sa.text("1.0")),
        sa.Column("source_id", sa.String(36), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("analyst_notes", sa.Text, nullable=True),
        sa.Column("event_time", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── entity_relationships ──────────────────────────────────────────────
    op.create_table(
        "entity_relationships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "source_entity_id", sa.String(36),
            sa.ForeignKey("entities.id", ondelete="CASCADE"), index=True,
        ),
        sa.Column(
            "target_entity_id", sa.String(36),
            sa.ForeignKey("entities.id", ondelete="CASCADE"), index=True,
        ),
        sa.Column("relationship_type", sa.String(50), index=True),
        sa.Column("confidence", sa.Float, server_default=sa.text("1.0")),
        sa.Column("attributes_json", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("bidirectional", sa.Boolean, server_default=sa.text("0")),
        sa.Column("analyst_notes", sa.Text, nullable=True),
        sa.Column("source_id", sa.String(36), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "modified_at", sa.DateTime,
            server_default=sa.func.now(), onupdate=sa.func.now(),
        ),
    )

    # ── entity_history ────────────────────────────────────────────────────
    op.create_table(
        "entity_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "entity_id", sa.String(36),
            sa.ForeignKey("entities.id", ondelete="CASCADE"), index=True,
        ),
        sa.Column("change_type", sa.String(50), index=True),
        sa.Column("field_name", sa.String(100), nullable=True),
        sa.Column("old_value", sa.Text, nullable=True),
        sa.Column("new_value", sa.Text, nullable=True),
        sa.Column("change_summary", sa.Text, nullable=True),
        sa.Column("changed_by", sa.String(100), nullable=True),
        sa.Column("source_id", sa.String(36), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("entity_history")
    op.drop_table("entity_relationships")
    op.drop_table("entity_events")
    op.drop_table("entity_observations")
    op.drop_table("entities")
