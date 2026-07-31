"""Add pipeline engine tables.

Revision ID: 006_pipeline_engine
Revises: 005_asset_library
Create Date: 2026-07-07
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006_pipeline_engine"
down_revision: str | None = "005_asset_library"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # pipelines table
    op.create_table(
        "pipelines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="SET NULL"), index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("template_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(50), default="pending", index=True),
        sa.Column("progress", sa.Float, default=0.0),
        sa.Column("owner", sa.String(100), nullable=True),
        sa.Column("priority", sa.Integer, default=0),
        sa.Column("total_nodes", sa.Integer, default=0),
        sa.Column("completed_nodes", sa.Integer, default=0),
        sa.Column("failed_nodes", sa.Integer, default=0),
        sa.Column("execution_time_ms", sa.Integer, default=0),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("modified_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # pipeline_nodes table
    op.create_table(
        "pipeline_nodes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("pipeline_id", sa.String(36), sa.ForeignKey("pipelines.id", ondelete="CASCADE"), index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("node_type", sa.String(50), nullable=False, index=True),
        sa.Column("status", sa.String(50), default="pending", index=True),
        sa.Column("inputs_json", sa.Text, nullable=True),
        sa.Column("outputs_json", sa.Text, nullable=True),
        sa.Column("parameters_json", sa.Text, nullable=True),
        sa.Column("depends_on_json", sa.Text, nullable=True),
        sa.Column("sort_order", sa.Integer, default=0),
        sa.Column("retry_count", sa.Integer, default=0),
        sa.Column("max_retries", sa.Integer, default=3),
        sa.Column("execution_time_ms", sa.Integer, default=0),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("result_json", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("modified_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("pipeline_id", "sort_order", name="uq_pipeline_node_order"),
    )

    # pipeline_history table
    op.create_table(
        "pipeline_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("pipeline_id", sa.String(36), sa.ForeignKey("pipelines.id", ondelete="CASCADE"), index=True),
        sa.Column("node_id", sa.String(36), sa.ForeignKey("pipeline_nodes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(50), nullable=False, index=True),
        sa.Column("details", sa.Text, nullable=True),
        sa.Column("performed_by", sa.String(100), nullable=True),
        sa.Column("execution_time_ms", sa.Integer, default=0),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # pipeline_queue table
    op.create_table(
        "pipeline_queue",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("pipeline_id", sa.String(36), sa.ForeignKey("pipelines.id", ondelete="CASCADE"), unique=True),
        sa.Column("status", sa.String(50), default="waiting", index=True),
        sa.Column("priority", sa.Integer, default=0),
        sa.Column("position", sa.Integer, default=0),
        sa.Column("worker_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # pipeline_logs table
    op.create_table(
        "pipeline_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("pipeline_id", sa.String(36), sa.ForeignKey("pipelines.id", ondelete="CASCADE"), index=True),
        sa.Column("node_id", sa.String(36), sa.ForeignKey("pipeline_nodes.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("details", sa.Text, nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("pipeline_logs")
    op.drop_table("pipeline_queue")
    op.drop_table("pipeline_history")
    op.drop_table("pipeline_nodes")
    op.drop_table("pipelines")
