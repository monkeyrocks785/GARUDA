"""Forecasting Framework Service.

Provides a pluggable forecasting framework with multiple algorithms.
Each algorithm extends the ForecastAlgorithm base class.
"""

import json
import logging
import math
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from sqlalchemy.orm import Session

from growth_engine.config import DEFAULT_CONFIDENCE_LEVEL, DEFAULT_FORECAST_STEPS, FORECAST_ALGORITHMS, MIN_HISTORY_POINTS
from growth_engine.database.models import ForecastModel, ForecastResult, GrowthHistory, GrowthMetric
from growth_engine.services.metric_service import MetricService
from knowledge_engine.database.models import Entity

logger = logging.getLogger("garuda.growth.forecast")


class ForecastAlgorithm(ABC):
    """Base class for all forecasting algorithms."""

    def __init__(self, parameters: dict | None = None):
        self.parameters = parameters or {}

    @abstractmethod
    def fit(self, x: np.ndarray, y: np.ndarray) -> "ForecastAlgorithm":
        ...

    @abstractmethod
    def predict(self, steps: int) -> np.ndarray:
        ...

    @abstractmethod
    def get_confidence_interval(self, steps: int, confidence_level: float = 0.95) -> tuple[np.ndarray, np.ndarray]:
        ...

    def get_fit_score(self, y_true: np.ndarray, y_pred: np.ndarray | None = None) -> float:
        if y_pred is None:
            return 0.0
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        if ss_tot == 0:
            return 0.0
        return float(max(0, 1 - ss_res / ss_tot))


class LinearRegressionForecast(ForecastAlgorithm):
    """Simple linear regression forecast."""

    def __init__(self, parameters: dict | None = None):
        super().__init__(parameters)
        self.slope: float = 0.0
        self.intercept: float = 0.0
        self.x_mean: float = 0.0
        self.y_std: float = 0.0
        self.n: int = 0

    def fit(self, x: np.ndarray, y: np.ndarray) -> "LinearRegressionForecast":
        self.n = len(x)
        if self.n < 2:
            raise ValueError(f"Need at least 2 data points, got {self.n}")
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        self.x_mean = float(x_mean)
        self.y_std = float(np.std(y)) if np.std(y) > 0 else 1.0
        num = np.sum((x - x_mean) * (y - y_mean))
        den = np.sum((x - x_mean) ** 2)
        self.slope = float(num / den) if den != 0 else 0.0
        self.intercept = float(y_mean - self.slope * x_mean)
        return self

    def predict(self, steps: int) -> np.ndarray:
        last_x = self.n - 1
        future_x = np.arange(last_x + 1, last_x + steps + 1)
        return self.slope * future_x + self.intercept

    def get_confidence_interval(self, steps: int, confidence_level: float = 0.95) -> tuple[np.ndarray, np.ndarray]:
        z = 1.96 if confidence_level >= 0.95 else 1.645
        pred = self.predict(steps)
        margin = z * self.y_std * (1 + 1 / self.n + (np.arange(steps) ** 2) / np.sum((np.arange(self.n) - self.x_mean) ** 2)) ** 0.5
        lower = pred - margin
        upper = pred + margin
        return lower, upper


class MovingAverageForecast(ForecastAlgorithm):
    """Moving average forecast using windowed averaging."""

    def __init__(self, parameters: dict | None = None):
        params = parameters or {}
        self.window = params.get("window", 3)
        self.y: np.ndarray = np.array([])
        super().__init__(parameters)

    def fit(self, x: np.ndarray, y: np.ndarray) -> "MovingAverageForecast":
        self.y = y
        self.n = len(y)
        if self.n < 2:
            raise ValueError(f"Need at least 2 data points, got {self.n}")
        self.window = min(self.window, self.n)
        return self

    def predict(self, steps: int) -> np.ndarray:
        if len(self.y) == 0:
            return np.zeros(steps)
        last_values = self.y[-self.window:]
        avg = np.mean(last_values)
        return np.full(steps, avg)

    def get_confidence_interval(self, steps: int, confidence_level: float = 0.95) -> tuple[np.ndarray, np.ndarray]:
        z = 1.96 if confidence_level >= 0.95 else 1.645
        pred = self.predict(steps)
        std = float(np.std(self.y[-self.window:])) if len(self.y) >= self.window else float(np.std(self.y))
        margin = z * std * np.sqrt(1 + 1 / self.window)
        lower = pred - margin
        upper = pred + margin
        lower = np.maximum(lower, 0)
        upper = np.maximum(upper, 0)
        return lower, upper


class PolynomialRegressionForecast(ForecastAlgorithm):
    """Polynomial regression forecast (degree configurable)."""

    def __init__(self, parameters: dict | None = None):
        params = parameters or {}
        self.degree = params.get("degree", 2)
        self.coeffs: np.ndarray = np.array([])
        self.n: int = 0
        self.y_std: float = 0.0
        super().__init__(parameters)

    def fit(self, x: np.ndarray, y: np.ndarray) -> "PolynomialRegressionForecast":
        self.n = len(x)
        if self.n < self.degree + 1:
            degree = max(1, self.n - 1)
            self.degree = degree
        self.coeffs = np.polyfit(x, y, self.degree)
        self.y_std = float(np.std(y)) if np.std(y) > 0 else 1.0
        return self

    def predict(self, steps: int) -> np.ndarray:
        if len(self.coeffs) == 0:
            return np.zeros(steps)
        last_x = self.n - 1
        future_x = np.arange(last_x + 1, last_x + steps + 1)
        return np.polyval(self.coeffs, future_x)

    def get_confidence_interval(self, steps: int, confidence_level: float = 0.95) -> tuple[np.ndarray, np.ndarray]:
        z = 1.96 if confidence_level >= 0.95 else 1.645
        pred = self.predict(steps)
        margin = z * self.y_std * np.sqrt(1 + 1 / self.n + (np.arange(steps) ** 2) / (self.n ** 2))
        lower = pred - margin
        upper = pred + margin
        lower = np.maximum(lower, 0)
        return lower, upper


class ExponentialTrendForecast(ForecastAlgorithm):
    """Exponential trend forecast (log-linear model)."""

    def __init__(self, parameters: dict | None = None):
        super().__init__(parameters)
        self.growth_rate: float = 0.0
        self.base_value: float = 0.0
        self.n: int = 0
        self.y_std: float = 0.0
        self.residual_std: float = 0.0

    def fit(self, x: np.ndarray, y: np.ndarray) -> "ExponentialTrendForecast":
        self.n = len(x)
        if self.n < 2:
            raise ValueError(f"Need at least 2 data points, got {self.n}")
        y_pos = np.maximum(y, 1e-10)
        log_y = np.log(y_pos)
        x_mean = np.mean(x)
        y_mean = np.mean(log_y)
        num = np.sum((x - x_mean) * (log_y - y_mean))
        den = np.sum((x - x_mean) ** 2)
        self.growth_rate = float(num / den) if den != 0 else 0.0
        log_base = float(y_mean - self.growth_rate * x_mean)
        self.base_value = float(np.exp(log_base))
        self.y_std = float(np.std(y)) if np.std(y) > 0 else 1.0
        residuals = log_y - (self.growth_rate * x + log_base)
        self.residual_std = float(np.std(residuals)) if len(residuals) > 1 else 0.1
        return self

    def predict(self, steps: int) -> np.ndarray:
        if self.growth_rate == 0:
            return np.full(steps, self.base_value)
        last_x = self.n - 1
        future_x = np.arange(last_x + 1, last_x + steps + 1)
        return self.base_value * np.exp(self.growth_rate * future_x)

    def get_confidence_interval(self, steps: int, confidence_level: float = 0.95) -> tuple[np.ndarray, np.ndarray]:
        z = 1.96 if confidence_level >= 0.95 else 1.645
        pred = self.predict(steps)
        margin = z * self.residual_std * pred
        lower = pred - margin
        upper = pred + margin
        lower = np.maximum(lower, 0)
        return lower, upper


ALGORITHM_MAP: dict[str, type[ForecastAlgorithm]] = {
    "linear_regression": LinearRegressionForecast,
    "moving_average": MovingAverageForecast,
    "polynomial_regression": PolynomialRegressionForecast,
    "exponential_trend": ExponentialTrendForecast,
}


class ForecastService:
    """Manages forecast generation, storage, and retrieval."""

    @staticmethod
    def get_available_algorithms() -> list[str]:
        return FORECAST_ALGORITHMS

    @staticmethod
    def generate_forecast(
        db: Session,
        project_id: str,
        entity_id: str,
        metric_name: str = "count",
        algorithm: str = "linear_regression",
        steps: int = DEFAULT_FORECAST_STEPS,
        confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
        algorithm_params: dict | None = None,
        step_unit: str = "months",
    ) -> dict[str, Any]:
        start = time.monotonic()

        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise ValueError(f"Entity not found: {entity_id}")

        if algorithm not in ALGORITHM_MAP:
            raise ValueError(f"Unsupported algorithm: {algorithm}. Supported: {list(ALGORITHM_MAP.keys())}")

        metrics = (
            db.query(GrowthMetric)
            .filter(
                GrowthMetric.entity_id == entity_id,
                GrowthMetric.metric_name == metric_name,
            )
            .order_by(GrowthMetric.observation_date.asc())
            .all()
        )

        if len(metrics) < MIN_HISTORY_POINTS:
            raise ValueError(
                f"Need at least {MIN_HISTORY_POINTS} data points for forecasting, "
                f"found {len(metrics)}"
            )

        values = [(m.observation_date, m.metric_value) for m in metrics if m.observation_date]
        first_date = values[0][0]
        last_date = values[-1][0]

        x = np.arange(len(values), dtype=float)
        y = np.array([v[1] for v in values], dtype=float)

        algo_class = ALGORITHM_MAP[algorithm]
        algo = algo_class(algorithm_params)
        algo.fit(x, y)

        y_pred = algo.predict(0)
        fit_score = algo.get_fit_score(y, np.full_like(y, np.mean(y)) if len(y_pred) == 0 else
                                        y_pred if len(y_pred) == len(y) else
                                        algo.predict(len(y)))

        future_pred = algo.predict(steps)
        ci_lower, ci_upper = algo.get_confidence_interval(steps, confidence_level)
        pr_lower = ci_lower * 0.9
        pr_upper = ci_upper * 1.1

        training_days = (last_date - first_date).days if first_date and last_date else 0

        params_record = algorithm_params or {}
        params_record["step_unit"] = step_unit
        params_record["steps"] = steps
        params_record["confidence_level"] = confidence_level

        fm = ForecastModel(
            project_id=project_id,
            entity_id=entity_id,
            entity_type=entity.entity_type,
            metric_name=metric_name,
            algorithm=algorithm,
            parameters_json=json.dumps(params_record),
            training_window_start=first_date,
            training_window_end=last_date,
            historical_fit_score=round(fit_score, 4),
            data_points=len(values),
        )
        db.add(fm)
        db.flush()

        forecast_results = []
        for i in range(steps):
            forecast_date: datetime
            if step_unit == "months":
                forecast_date = last_date + timedelta(days=30 * (i + 1)) if last_date else datetime.utcnow()
            elif step_unit == "years":
                forecast_date = last_date + timedelta(days=365 * (i + 1)) if last_date else datetime.utcnow()
            elif step_unit == "weeks":
                forecast_date = last_date + timedelta(weeks=i + 1) if last_date else datetime.utcnow()
            else:
                forecast_date = last_date + timedelta(days=i + 1) if last_date else datetime.utcnow()

            pred_val = max(0, float(future_pred[i]))
            ci_l = max(0, float(ci_lower[i]))
            ci_u = max(0, float(ci_upper[i]))
            pr_l = max(0, float(pr_lower[i]))
            pr_u = max(0, float(pr_upper[i]))

            fr = ForecastResult(
                project_id=project_id,
                entity_id=entity_id,
                entity_type=entity.entity_type,
                forecast_model_id=fm.id,
                metric_name=metric_name,
                algorithm=algorithm,
                forecast_date=forecast_date,
                predicted_value=pred_val,
                confidence_interval_lower=ci_l,
                confidence_interval_upper=ci_u,
                prediction_range_lower=pr_l,
                prediction_range_upper=pr_u,
                confidence_level=confidence_level,
                historical_fit_score=round(fit_score, 4),
                training_window_days=training_days,
            )
            db.add(fr)
            forecast_results.append(fr.to_dict())

        db.commit()

        elapsed = (time.monotonic() - start) * 1000

        history = GrowthHistory(
            project_id=project_id,
            calculation_type="forecast",
            parameters_json=json.dumps({
                "entity_id": entity_id,
                "metric_name": metric_name,
                "algorithm": algorithm,
                "steps": steps,
            }),
            result_summary_json=json.dumps({
                "model_id": fm.id,
                "forecast_count": len(forecast_results),
                "fit_score": round(fit_score, 4),
            }),
            result_count=len(forecast_results),
            execution_time_ms=round(elapsed, 2),
        )
        db.add(history)
        db.commit()

        return {
            "project_id": project_id,
            "entity_id": entity_id,
            "entity_type": entity.entity_type,
            "metric_name": metric_name,
            "algorithm": algorithm,
            "model_id": fm.id,
            "historical_data_points": len(values),
            "historical_fit_score": round(fit_score, 4),
            "training_window_start": first_date.isoformat() if first_date else None,
            "training_window_end": last_date.isoformat() if last_date else None,
            "training_window_days": training_days,
            "forecast": forecast_results,
            "execution_time_ms": round(elapsed, 2),
        }

    @staticmethod
    def get_entity_forecasts(
        db: Session,
        entity_id: str,
        limit: int = 50,
    ) -> list[dict]:
        results = (
            db.query(ForecastResult)
            .filter(ForecastResult.entity_id == entity_id)
            .order_by(ForecastResult.forecast_date.desc())
            .limit(limit)
            .all()
        )
        return [r.to_dict() for r in results]

    @staticmethod
    def get_project_forecasts(
        db: Session,
        project_id: str,
        entity_type: str | None = None,
        metric_name: str | None = None,
        page: int = 0,
        page_size: int = 50,
    ) -> tuple[list[dict], int]:
        q = db.query(ForecastResult).filter(ForecastResult.project_id == project_id)
        if entity_type:
            q = q.filter(ForecastResult.entity_type == entity_type)
        if metric_name:
            q = q.filter(ForecastResult.metric_name == metric_name)
        total = q.count()
        items = q.order_by(ForecastResult.forecast_date.desc()).offset(page * page_size).limit(page_size).all()
        return [r.to_dict() for r in items], total

    @staticmethod
    def get_forecast_models(
        db: Session,
        project_id: str,
        entity_id: str | None = None,
        active_only: bool = True,
    ) -> list[dict]:
        q = db.query(ForecastModel).filter(ForecastModel.project_id == project_id)
        if entity_id:
            q = q.filter(ForecastModel.entity_id == entity_id)
        if active_only:
            q = q.filter(ForecastModel.is_active == True)
        q = q.order_by(ForecastModel.created_at.desc())
        return [m.to_dict() for m in q.all()]
