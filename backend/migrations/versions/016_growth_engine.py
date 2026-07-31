"""016 - Growth Analytics Engine

Revision ID: 016_growth_engine
Revises: 015_query_engine
Create Date: 2026-07-22
"""

from alembic import op
import sqlalchemy as sa

revision = "016_growth_engine"
down_revision = "015_query_engine"


def upgrade() -> None:
    op.create_table(
        "growth_metrics",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), index=True),
        sa.Column("entity_id", sa.String(36), index=True),
        sa.Column("entity_type", sa.String(50), index=True),
        sa.Column("metric_name", sa.String(50), index=True),
        sa.Column("metric_value", sa.Float),
        sa.Column("unit", sa.String(50)),
        sa.Column("confidence", sa.Float, server_default=sa.text("1.0")),
        sa.Column("observation_id", sa.String(36), nullable=True),
        sa.Column("observation_date", sa.DateTime, nullable=True),
        sa.Column("attributes_json", sa.Text, nullable=True),
        sa.Column("computed_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "growth_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), index=True),
        sa.Column("entity_id", sa.String(36), nullable=True, index=True),
        sa.Column("calculation_type", sa.String(50), index=True),
        sa.Column("parameters_json", sa.Text, nullable=True),
        sa.Column("result_summary_json", sa.Text, nullable=True),
        sa.Column("result_count", sa.Integer, server_default=sa.text("0")),
        sa.Column("execution_time_ms", sa.Float, server_default=sa.text("0.0")),
        sa.Column("status", sa.String(50), server_default="completed"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("executed_by", sa.String(100), nullable=True),
        sa.Column("executed_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "forecast_models",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), index=True),
        sa.Column("entity_id", sa.String(36), index=True),
        sa.Column("entity_type", sa.String(50)),
        sa.Column("metric_name", sa.String(50)),
        sa.Column("algorithm", sa.String(50)),
        sa.Column("parameters_json", sa.Text, nullable=True),
        sa.Column("training_window_start", sa.DateTime, nullable=True),
        sa.Column("training_window_end", sa.DateTime, nullable=True),
        sa.Column("historical_fit_score", sa.Float, server_default=sa.text("0.0")),
        sa.Column("data_points", sa.Integer, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "modified_at", sa.DateTime,
            server_default=sa.func.now(), onupdate=sa.func.now(),
        ),
    )

    op.create_table(
        "forecast_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), index=True),
        sa.Column("entity_id", sa.String(36), index=True),
        sa.Column("entity_type", sa.String(50)),
        sa.Column("forecast_model_id", sa.String(36), nullable=True),
        sa.Column("metric_name", sa.String(50)),
        sa.Column("algorithm", sa.String(50)),
        sa.Column("forecast_date", sa.DateTime, index=True),
        sa.Column("predicted_value", sa.Float),
        sa.Column("confidence_interval_lower", sa.Float),
        sa.Column("confidence_interval_upper", sa.Float),
        sa.Column("prediction_range_lower", sa.Float),
        sa.Column("prediction_range_upper", sa.Float),
        sa.Column("confidence_level", sa.Float, server_default=sa.text("0.95")),
        sa.Column("historical_fit_score", sa.Float, server_default=sa.text("0.0")),
        sa.Column("training_window_days", sa.Integer, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("forecast_results")
    op.drop_table("forecast_models")
    op.drop_table("growth_history")
    op.drop_table("growth_metrics")
