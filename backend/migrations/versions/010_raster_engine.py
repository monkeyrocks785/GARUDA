"""Raster Processing Engine migration.

Revision ID: 010_raster_engine
Create Date: 2025-01-16
"""

import sqlalchemy as sa
from alembic import op

revision = "010_raster_engine"
down_revision = "009_workspace_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Raster Metadata
    op.create_table(
        "raster_metadata",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "dataset_id",
            sa.String(36),
            sa.ForeignKey("datasets.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("file_path", sa.Text, nullable=False),
        sa.Column("width", sa.Integer, nullable=False),
        sa.Column("height", sa.Integer, nullable=False),
        sa.Column("band_count", sa.Integer, nullable=False),
        sa.Column("data_type", sa.String(50), nullable=False),
        sa.Column("nodata_value", sa.Float, nullable=True),
        sa.Column("crs", sa.String(100), nullable=False),
        sa.Column("resolution_x", sa.Float, nullable=False),
        sa.Column("resolution_y", sa.Float, nullable=False),
        sa.Column("pixel_size_x", sa.Float, nullable=False),
        sa.Column("pixel_size_y", sa.Float, nullable=False),
        sa.Column("bounds_min_x", sa.Float, nullable=False),
        sa.Column("bounds_min_y", sa.Float, nullable=False),
        sa.Column("bounds_max_x", sa.Float, nullable=False),
        sa.Column("bounds_max_y", sa.Float, nullable=False),
        sa.Column("transform", sa.Text, nullable=True),
        sa.Column("bands_info", sa.Text, nullable=True),
        sa.Column("compression", sa.String(50), nullable=True),
        sa.Column("file_format", sa.String(50), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("has_overviews", sa.Boolean, server_default="0"),
        sa.Column("overview_levels", sa.Text, nullable=True),
        sa.Column("statistics", sa.Text, nullable=True),
        sa.Column("histogram", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Processing History
    op.create_table(
        "raster_processing_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "dataset_id",
            sa.String(36),
            sa.ForeignKey("datasets.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("operation", sa.String(100), nullable=False),
        sa.Column("parameters", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("input_path", sa.Text, nullable=True),
        sa.Column("output_path", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("execution_time_ms", sa.Integer, nullable=True),
        sa.Column("pipeline_id", sa.String(36), nullable=True, index=True),
        sa.Column("node_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    # Derived Products
    op.create_table(
        "raster_derived_products",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "source_dataset_id",
            sa.String(36),
            sa.ForeignKey("datasets.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("asset_id", sa.String(36), nullable=True, index=True),
        sa.Column("operation", sa.String(100), nullable=False),
        sa.Column("output_path", sa.Text, nullable=False),
        sa.Column("output_filename", sa.String(255), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("parameters", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("raster_derived_products")
    op.drop_table("raster_processing_history")
    op.drop_table("raster_metadata")
