"""Image Registration Engine migration.

Revision ID: 011_registration_engine
Revises: 010_raster_engine
Create Date: 2025-01-20
"""

import sqlalchemy as sa
from alembic import op

revision = "011_registration_engine"
down_revision = "010_raster_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # image_registrations
    op.create_table(
        "image_registrations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("reference_path", sa.Text, nullable=False),
        sa.Column("target_path", sa.Text, nullable=False),
        sa.Column("output_path", sa.Text, nullable=True),
        sa.Column("mode", sa.String(50), server_default="automatic"),
        sa.Column("feature_detector", sa.String(50), server_default="orb"),
        sa.Column("feature_matcher", sa.String(50), server_default="bf"),
        sa.Column("transform_type", sa.String(50), server_default="affine"),
        sa.Column("resampling", sa.String(50), server_default="bilinear"),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("ref_width", sa.Integer, nullable=True),
        sa.Column("ref_height", sa.Integer, nullable=True),
        sa.Column("ref_crs", sa.String(100), nullable=True),
        sa.Column("ref_resolution", sa.Text, nullable=True),
        sa.Column("tgt_width", sa.Integer, nullable=True),
        sa.Column("tgt_height", sa.Integer, nullable=True),
        sa.Column("tgt_crs", sa.String(100), nullable=True),
        sa.Column("tgt_resolution", sa.Text, nullable=True),
        sa.Column("transform_matrix", sa.Text, nullable=True),
        sa.Column("rmse", sa.Float, nullable=True),
        sa.Column("matched_points", sa.Integer, nullable=True),
        sa.Column("inlier_count", sa.Integer, nullable=True),
        sa.Column("inlier_ratio", sa.Float, nullable=True),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("pipeline_id", sa.String(36), nullable=True, index=True),
        sa.Column("favorite", sa.Boolean, server_default="0"),
        sa.Column("archived", sa.Boolean, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    # control_points
    op.create_table(
        "control_points",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "registration_id",
            sa.String(36),
            sa.ForeignKey("image_registrations.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("point_index", sa.Integer, nullable=False),
        sa.Column("ref_x", sa.Float, nullable=False),
        sa.Column("ref_y", sa.Float, nullable=False),
        sa.Column("target_x", sa.Float, nullable=False),
        sa.Column("target_y", sa.Float, nullable=False),
        sa.Column("ref_lon", sa.Float, nullable=True),
        sa.Column("ref_lat", sa.Float, nullable=True),
        sa.Column("target_lon", sa.Float, nullable=True),
        sa.Column("target_lat", sa.Float, nullable=True),
        sa.Column("residual", sa.Float, nullable=True),
        sa.Column("is_inlier", sa.Boolean, server_default="1"),
        sa.Column("label", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # registration_history
    op.create_table(
        "registration_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "registration_id",
            sa.String(36),
            sa.ForeignKey("image_registrations.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("operation", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("parameters", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("execution_time_ms", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    # registration_metrics
    op.create_table(
        "registration_metrics",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "registration_id",
            sa.String(36),
            sa.ForeignKey("image_registrations.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("features_detected_ref", sa.Integer, nullable=True),
        sa.Column("features_detected_tgt", sa.Integer, nullable=True),
        sa.Column("raw_matches", sa.Integer, nullable=True),
        sa.Column("good_matches", sa.Integer, nullable=True),
        sa.Column("inlier_matches", sa.Integer, nullable=True),
        sa.Column("transform_determinant", sa.Float, nullable=True),
        sa.Column("max_residual", sa.Float, nullable=True),
        sa.Column("median_residual", sa.Float, nullable=True),
        sa.Column("overall_score", sa.Float, nullable=True),
        sa.Column("quality_grade", sa.String(20), nullable=True),
        sa.Column("raw_metrics", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("registration_metrics")
    op.drop_table("registration_history")
    op.drop_table("control_points")
    op.drop_table("image_registrations")
