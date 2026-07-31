"""Add asset library tables

Revision ID: 005_asset_library
Revises: 004_data_engine
Create Date: 2026-07-07
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "005_asset_library"
down_revision = "004_data_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # assets table
    op.create_table(
        "assets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="SET NULL"), index=True),
        sa.Column("name", sa.String(500), nullable=False, index=True),
        sa.Column("display_name", sa.String(500), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("asset_type", sa.String(50), nullable=False, index=True),
        sa.Column("category", sa.String(50), nullable=True, index=True),
        sa.Column("extension", sa.String(20), nullable=False, index=True),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column("preview_path", sa.String(1000), nullable=True),
        sa.Column("thumbnail_path", sa.String(1000), nullable=True),
        sa.Column("file_size", sa.Integer, default=0),
        sa.Column("checksum", sa.String(64), nullable=False, index=True),
        sa.Column("owner", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), default="active", index=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("is_favorite", sa.Boolean, default=False, index=True),
        sa.Column("is_pinned", sa.Boolean, default=False),
        sa.Column("is_archived", sa.Boolean, default=False, index=True),
        sa.Column("is_hidden", sa.Boolean, default=False),
        sa.Column("metadata_json", sa.Text, nullable=True),
        sa.Column("tags", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("modified_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )

    # asset_versions table
    op.create_table(
        "asset_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("asset_id", sa.String(36), sa.ForeignKey("assets.id", ondelete="CASCADE"), index=True),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("file_size", sa.Integer, default=0),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column("change_description", sa.Text, default="Initial version"),
        sa.Column("changed_by", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # asset_relationships table
    op.create_table(
        "asset_relationships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_asset_id", sa.String(36), sa.ForeignKey("assets.id", ondelete="CASCADE"), index=True),
        sa.Column("target_asset_id", sa.String(36), sa.ForeignKey("assets.id", ondelete="CASCADE"), index=True),
        sa.Column("relationship_type", sa.String(50), nullable=False, index=True),
        sa.Column("metadata_json", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("source_asset_id", "target_asset_id", "relationship_type", name="uq_asset_relationship"),
    )

    # collections table
    op.create_table(
        "collections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="SET NULL"), index=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("color", sa.String(20), nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("owner", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("modified_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # collection_assets table
    op.create_table(
        "collection_assets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("collection_id", sa.String(36), sa.ForeignKey("collections.id", ondelete="CASCADE"), index=True),
        sa.Column("asset_id", sa.String(36), sa.ForeignKey("assets.id", ondelete="CASCADE"), index=True),
        sa.Column("sort_order", sa.Integer, default=0),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("collection_id", "asset_id", name="uq_collection_asset"),
    )

    # asset_tags table
    op.create_table(
        "asset_tags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("asset_id", sa.String(36), sa.ForeignKey("assets.id", ondelete="CASCADE"), index=True),
        sa.Column("tag", sa.String(100), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("asset_id", "tag", name="uq_asset_tag"),
    )

    # asset_history table
    op.create_table(
        "asset_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("asset_id", sa.String(36), sa.ForeignKey("assets.id", ondelete="CASCADE"), index=True),
        sa.Column("action", sa.String(50), nullable=False, index=True),
        sa.Column("details", sa.Text, nullable=True),
        sa.Column("performed_by", sa.String(100), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("asset_history")
    op.drop_table("asset_tags")
    op.drop_table("collection_assets")
    op.drop_table("collections")
    op.drop_table("asset_relationships")
    op.drop_table("asset_versions")
    op.drop_table("assets")
