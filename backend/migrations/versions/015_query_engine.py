"""015 - Intelligence Query Engine

Revision ID: 015_query_engine
Revises: 014_knowledge_engine
Create Date: 2026-07-08
"""

from alembic import op
import sqlalchemy as sa

revision = "015_query_engine"
down_revision = "014_knowledge_engine"


def upgrade() -> None:
    op.create_table(
        "saved_queries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), index=True),
        sa.Column("name", sa.String(255)),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("filters_json", sa.Text),
        sa.Column("sort_by", sa.String(50), nullable=True),
        sa.Column("sort_direction", sa.String(10), server_default="asc"),
        sa.Column("max_results", sa.Integer, server_default=sa.text("500")),
        sa.Column("favorite", sa.Boolean, server_default=sa.text("0")),
        sa.Column("pinned", sa.Boolean, server_default=sa.text("0")),
        sa.Column("tags_json", sa.Text, nullable=True),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "modified_at", sa.DateTime,
            server_default=sa.func.now(), onupdate=sa.func.now(),
        ),
    )

    op.create_table(
        "query_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), index=True),
        sa.Column("saved_query_id", sa.String(36), nullable=True, index=True),
        sa.Column("filters_json", sa.Text),
        sa.Column("result_count", sa.Integer, server_default=sa.text("0")),
        sa.Column("execution_time_ms", sa.Float, server_default=sa.text("0.0")),
        sa.Column("status", sa.String(50), server_default="completed"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("executed_by", sa.String(100), nullable=True),
        sa.Column("executed_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "query_results_cache",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("query_hash", sa.String(64), index=True),
        sa.Column("project_id", sa.String(36), index=True),
        sa.Column("results_json", sa.Text),
        sa.Column("total_count", sa.Integer, server_default=sa.text("0")),
        sa.Column("execution_time_ms", sa.Float, server_default=sa.text("0.0")),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("query_results_cache")
    op.drop_table("query_history")
    op.drop_table("saved_queries")
