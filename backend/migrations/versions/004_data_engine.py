"""Add data engine tables

Revision ID: 004_data_engine
Revises: 003_geospatial
Create Date: 2026-07-06
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "004_data_engine"
down_revision = "003_geospatial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # datasets table
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), index=True),
        sa.Column("name", sa.String(500), nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("dataset_type", sa.String(50), nullable=False, index=True),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("internal_filename", sa.String(500), nullable=False),
        sa.Column("extension", sa.String(20), nullable=False, index=True),
        sa.Column("coordinate_system", sa.String(50), nullable=True),
        sa.Column("bbox_min_x", sa.Float, nullable=True),
        sa.Column("bbox_min_y", sa.Float, nullable=True),
        sa.Column("bbox_max_x", sa.Float, nullable=True),
        sa.Column("bbox_max_y", sa.Float, nullable=True),
        sa.Column("resolution_x", sa.Float, nullable=True),
        sa.Column("resolution_y", sa.Float, nullable=True),
        sa.Column("bands", sa.Integer, nullable=True),
        sa.Column("width", sa.Integer, nullable=True),
        sa.Column("height", sa.Integer, nullable=True),
        sa.Column("file_size", sa.Integer, default=0),
        sa.Column("checksum", sa.String(64), nullable=False, index=True),
        sa.Column("status", sa.String(50), default="importing", index=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("is_favorite", sa.Boolean, default=False, index=True),
        sa.Column("is_archived", sa.Boolean, default=False, index=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("imported_by", sa.String(100), nullable=True),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column("thumbnail_path", sa.String(1000), nullable=True),
        sa.Column("metadata_json", sa.Text, nullable=True),
        sa.Column("tags", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("modified_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # dataset_versions table
    op.create_table(
        "dataset_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id", ondelete="CASCADE"), index=True),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("file_size", sa.Integer, default=0),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column("internal_filename", sa.String(500), nullable=False),
        sa.Column("change_description", sa.Text, default="Initial import"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # dataset_tags table
    op.create_table(
        "dataset_tags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id", ondelete="CASCADE"), index=True),
        sa.Column("tag", sa.String(100), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("dataset_id", "tag", name="uq_dataset_tag"),
    )

    # dataset_metadata table
    op.create_table(
        "dataset_metadata",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id", ondelete="CASCADE"), index=True),
        sa.Column("key", sa.String(255), nullable=False, index=True),
        sa.Column("value", sa.Text, nullable=True),
        sa.Column("category", sa.String(50), default="general"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("dataset_id", "key", name="uq_dataset_metadata_key"),
    )


def downgrade() -> None:
    op.drop_table("dataset_metadata")
    op.drop_table("dataset_tags")
    op.drop_table("dataset_versions")
    op.drop_table("datasets")
