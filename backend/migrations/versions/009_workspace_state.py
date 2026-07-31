"""Workspace State migration.

Revision ID: 009_workspace_state
Create Date: 2025-01-15
"""

import sqlalchemy as sa
from alembic import op

revision = "009_workspace_state"
down_revision = "008_temporal_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspace_states",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            unique=True,
        ),
        sa.Column("zoom", sa.Float, server_default="2.0"),
        sa.Column("center_lat", sa.Float, server_default="20.0"),
        sa.Column("center_lng", sa.Float, server_default="0.0"),
        sa.Column("map_rotation", sa.Float, server_default="0.0"),
        sa.Column("basemap", sa.String(50), server_default="blank_grid"),
        sa.Column("active_tool", sa.String(50), nullable=True),
        sa.Column("selected_layer_id", sa.String(36), nullable=True),
        sa.Column("selected_object_id", sa.String(36), nullable=True),
        sa.Column("selected_object_type", sa.String(50), nullable=True),
        sa.Column("visible_layers", sa.Text, nullable=True),
        sa.Column("panel_layout", sa.Text, nullable=True),
        sa.Column("drawing_features", sa.Text, nullable=True),
        sa.Column("measurement_features", sa.Text, nullable=True),
        sa.Column("undo_stack", sa.Text, nullable=True),
        sa.Column("redo_stack", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("workspace_states")
