"""018 - GIS Workspace additions

Adds a per-layer CRS column and the gis_basemaps registry table.

Revision ID: 018_gis_workspace
Revises: 017_rules_engine
Create Date: 2026-07-31
"""

import sqlalchemy as sa
from alembic import op

revision = "018_gis_workspace"
down_revision = "017_rules_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("layers", sa.Column("crs", sa.String(50), nullable=True))
    op.create_table(
        "gis_basemaps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("basemap_type", sa.String(50), nullable=False),
        sa.Column("path", sa.Text, nullable=False),
        sa.Column("crs", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_gis_basemaps_basemap_type", "gis_basemaps", ["basemap_type"])


def downgrade() -> None:
    op.drop_index("ix_gis_basemaps_basemap_type", table_name="gis_basemaps")
    op.drop_table("gis_basemaps")
    op.drop_column("layers", "crs")
