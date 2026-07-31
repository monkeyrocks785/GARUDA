"""Create geospatial tables (aois, layers, imported_files, project_map_states).

Revision ID: 003_geospatial
Revises: 002_projects
Create Date: 2024-01-03 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003_geospatial"
down_revision: str | None = "002_projects"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # AOI table
    op.create_table(
        "aois",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("geometry", sa.Text, nullable=False),
        sa.Column("geometry_type", sa.String(50), nullable=False),
        sa.Column("bbox", sa.Text, nullable=True),
        sa.Column("area_m2", sa.Float, nullable=True),
        sa.Column("fill_color", sa.String(20), server_default="#3388ff"),
        sa.Column("fill_opacity", sa.Float, server_default="0.2"),
        sa.Column("stroke_color", sa.String(20), server_default="#3388ff"),
        sa.Column("stroke_width", sa.Float, server_default="2.0"),
        sa.Column("source", sa.String(50), server_default="manual"),
        sa.Column("source_file", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_aois_project_id", "aois", ["project_id"])

    # Layer table
    op.create_table(
        "layers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("layer_type", sa.String(50), nullable=False),
        sa.Column("visible", sa.Boolean, server_default="1"),
        sa.Column("opacity", sa.Float, server_default="1.0"),
        sa.Column("z_index", sa.Integer, server_default="0"),
        sa.Column("source_id", sa.String(36), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("style", sa.Text, nullable=True),
        sa.Column("extra_metadata", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_layers_project_id", "layers", ["project_id"])
    op.create_index("ix_layers_layer_type", "layers", ["layer_type"])

    # Imported files table
    op.create_table(
        "imported_files",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=False),
        sa.Column("file_size", sa.Integer, server_default="0"),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("geometry_type", sa.String(50), nullable=True),
        sa.Column("feature_count", sa.Integer, server_default="0"),
        sa.Column("is_valid", sa.Boolean, server_default="1"),
        sa.Column("validation_errors", sa.Text, nullable=True),
        sa.Column("layer_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_imported_files_project_id", "imported_files", ["project_id"])
    op.create_index("ix_imported_files_file_type", "imported_files", ["file_type"])

    # Project map state table
    op.create_table(
        "project_map_states",
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("zoom", sa.Float, server_default="2.0"),
        sa.Column("center_lat", sa.Float, server_default="20.0"),
        sa.Column("center_lng", sa.Float, server_default="0.0"),
        sa.Column("map_rotation", sa.Float, server_default="0.0"),
        sa.Column("basemap", sa.String(100), server_default="osm"),
        sa.Column("visible_layers", sa.Text, nullable=True),
        sa.Column("selected_layer_id", sa.String(36), nullable=True),
        sa.Column("sidebar_width", sa.Integer, server_default="280"),
        sa.Column("panel_visible", sa.Boolean, server_default="1"),
        sa.Column("active_tool", sa.String(50), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("project_map_states")
    op.drop_index("ix_imported_files_file_type")
    op.drop_index("ix_imported_files_project_id")
    op.drop_table("imported_files")
    op.drop_index("ix_layers_layer_type")
    op.drop_index("ix_layers_project_id")
    op.drop_table("layers")
    op.drop_index("ix_aois_project_id")
    op.drop_table("aois")
