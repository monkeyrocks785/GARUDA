"""Database models for the Growth Analytics Engine.

Stores growth metrics, calculation history, forecast models, and forecast results.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class GrowthMetric(Base):
    """A computed metric value for an entity at a point in time."""

    __tablename__ = "growth_metrics"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="CASCADE"), index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    metric_name: Mapped[str] = mapped_column(String(50), index=True)
    metric_value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    observation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    observation_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    attributes_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "unit": self.unit,
            "confidence": self.confidence,
            "observation_id": self.observation_id,
            "observation_date": self.observation_date.isoformat()
                if self.observation_date else None,
            "attributes_json": self.attributes_json,
            "computed_at": self.computed_at.isoformat() if self.computed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class GrowthHistory(Base):
    """A record of a growth calculation or analysis run."""

    __tablename__ = "growth_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    calculation_type: Mapped[str] = mapped_column(String(50), index=True)
    parameters_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="completed")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "entity_id": self.entity_id,
            "calculation_type": self.calculation_type,
            "parameters_json": self.parameters_json,
            "result_summary_json": self.result_summary_json,
            "result_count": self.result_count,
            "execution_time_ms": self.execution_time_ms,
            "status": self.status,
            "error_message": self.error_message,
            "executed_by": self.executed_by,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }


class ForecastModel(Base):
    """A trained forecast model configuration."""

    __tablename__ = "forecast_models"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="CASCADE"), index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50))
    metric_name: Mapped[str] = mapped_column(String(50))
    algorithm: Mapped[str] = mapped_column(String(50))
    parameters_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    training_window_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    training_window_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    historical_fit_score: Mapped[float] = mapped_column(Float, default=0.0)
    data_points: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "metric_name": self.metric_name,
            "algorithm": self.algorithm,
            "parameters_json": self.parameters_json,
            "training_window_start": self.training_window_start.isoformat()
                if self.training_window_start else None,
            "training_window_end": self.training_window_end.isoformat()
                if self.training_window_end else None,
            "historical_fit_score": self.historical_fit_score,
            "data_points": self.data_points,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
        }


class ForecastResult(Base):
    """A computed forecast value with uncertainty bounds."""

    __tablename__ = "forecast_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="CASCADE"), index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50))
    forecast_model_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("forecast_models.id", ondelete="SET NULL"), nullable=True
    )
    metric_name: Mapped[str] = mapped_column(String(50))
    algorithm: Mapped[str] = mapped_column(String(50))
    forecast_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    predicted_value: Mapped[float] = mapped_column(Float)
    confidence_interval_lower: Mapped[float] = mapped_column(Float)
    confidence_interval_upper: Mapped[float] = mapped_column(Float)
    prediction_range_lower: Mapped[float] = mapped_column(Float)
    prediction_range_upper: Mapped[float] = mapped_column(Float)
    confidence_level: Mapped[float] = mapped_column(Float, default=0.95)
    historical_fit_score: Mapped[float] = mapped_column(Float, default=0.0)
    training_window_days: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "forecast_model_id": self.forecast_model_id,
            "metric_name": self.metric_name,
            "algorithm": self.algorithm,
            "forecast_date": self.forecast_date.isoformat()
                if self.forecast_date else None,
            "predicted_value": self.predicted_value,
            "confidence_interval_lower": self.confidence_interval_lower,
            "confidence_interval_upper": self.confidence_interval_upper,
            "prediction_range_lower": self.prediction_range_lower,
            "prediction_range_upper": self.prediction_range_upper,
            "confidence_level": self.confidence_level,
            "historical_fit_score": self.historical_fit_score,
            "training_window_days": self.training_window_days,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
