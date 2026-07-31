"""Intelligence Analysis Engine migration.

Revision ID: 013_intelligence_engine
Revises: 012_comparison_engine
Create Date: 2025-07-08
"""
import sqlalchemy as sa
from alembic import op

revision = "013_intelligence_engine"
down_revision = "012_comparison_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Registered Models ────────────────────────────────────────────────
    op.create_table(
        "registered_models",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("version", sa.String(50), nullable=False, server_default="1.0.0"),
        sa.Column("task", sa.String(50), nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("license", sa.String(255), nullable=True),
        sa.Column("framework", sa.String(50), nullable=False, server_default="pytorch"),
        sa.Column("input_type", sa.String(50), nullable=False, server_default="raster"),
        sa.Column("output_type", sa.String(50), nullable=False, server_default="detections"),
        sa.Column("weights_path", sa.Text, nullable=True),
        sa.Column("weights_checksum", sa.String(64), nullable=True),
        sa.Column("config_json", sa.Text, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="registered", index=True),
        sa.Column("is_loaded", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("gpu_required", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("class_names_json", sa.Text, nullable=True),
        sa.Column("default_params_json", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("last_loaded_at", sa.DateTime, nullable=True),
        sa.Column("inference_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("favorite", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("archived", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("modified_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ── Analysis Jobs ────────────────────────────────────────────────────
    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "project_id", sa.String(36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column(
            "model_id", sa.String(36),
            sa.ForeignKey("registered_models.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("task_type", sa.String(50), nullable=False, index=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending", index=True),
        sa.Column("input_path", sa.Text, nullable=True),
        sa.Column("input_type", sa.String(50), nullable=True),
        sa.Column("output_path", sa.Text, nullable=True),
        sa.Column("parameters_json", sa.Text, nullable=True),
        sa.Column("progress", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("total_items", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("processed_items", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("detection_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("execution_time_ms", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("tile_size", sa.Integer, nullable=False, server_default=sa.text("512")),
        sa.Column("tile_overlap", sa.Integer, nullable=False, server_default=sa.text("64")),
        sa.Column("batch_size", sa.Integer, nullable=False, server_default=sa.text("8")),
        sa.Column("confidence_threshold", sa.Float, nullable=False, server_default=sa.text("0.5")),
        sa.Column("iou_threshold", sa.Float, nullable=False, server_default=sa.text("0.45")),
        sa.Column("device", sa.String(20), nullable=False, server_default="cpu"),
        sa.Column("cancel_requested", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("resume_token", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "result_asset_id", sa.String(36),
            sa.ForeignKey("assets.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("favorite", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("archived", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("modified_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ── Detections ───────────────────────────────────────────────────────
    op.create_table(
        "detections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "job_id", sa.String(36),
            sa.ForeignKey("analysis_jobs.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column(
            "project_id", sa.String(36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column(
            "model_id", sa.String(36),
            sa.ForeignKey("registered_models.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("class_name", sa.String(100), nullable=False, index=True),
        sa.Column("class_id", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("confidence", sa.Float, nullable=False, index=True),
        sa.Column("geometry_json", sa.Text, nullable=False),
        sa.Column("bbox_min_x", sa.Float, nullable=False),
        sa.Column("bbox_min_y", sa.Float, nullable=False),
        sa.Column("bbox_max_x", sa.Float, nullable=False),
        sa.Column("bbox_max_y", sa.Float, nullable=False),
        sa.Column("centroid_x", sa.Float, nullable=False),
        sa.Column("centroid_y", sa.Float, nullable=False),
        sa.Column("area", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("execution_time_ms", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("processing_params_json", sa.Text, nullable=True),
        sa.Column("tile_x", sa.Integer, nullable=True),
        sa.Column("tile_y", sa.Integer, nullable=True),
        sa.Column("review_status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("reviewer_notes", sa.Text, nullable=True),
        sa.Column("reviewed_at", sa.DateTime, nullable=True),
        sa.Column("reviewed_by", sa.String(100), nullable=True),
        sa.Column("edited_geometry_json", sa.Text, nullable=True),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # ── Analysis History ─────────────────────────────────────────────────
    op.create_table(
        "analysis_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), nullable=False, index=True),
        sa.Column("action", sa.String(50), nullable=False, index=True),
        sa.Column("details", sa.Text, nullable=True),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", sa.String(36), nullable=True),
        sa.Column("timestamp", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("analysis_history")
    op.drop_table("detections")
    op.drop_table("analysis_jobs")
    op.drop_table("registered_models")
