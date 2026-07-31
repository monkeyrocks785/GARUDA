"""Tests for the Growth Analytics Engine."""

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def get_test_project() -> str:
    unique_name = f"Growth Test {uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/projects",
        json={"name": unique_name, "description": "Growth engine test project"},
    )
    assert r.status_code == 201
    return r.json()["id"]


def create_test_entity(
    project_id: str,
    entity_type: str = "building",
    name: str | None = None,
) -> str:
    if name is None:
        name = f"GRW-{uuid.uuid4().hex[:6]}"
    r = client.post(
        f"/api/v1/knowledge/project/{project_id}/entities",
        json={"entity_type": entity_type, "name": name},
    )
    assert r.status_code == 201
    return r.json()["id"]


def add_observation(
    entity_id: str,
    attributes: dict | None = None,
    observed_at: str | None = None,
) -> str:
    payload = {"observation_type": "measurement"}
    if attributes:
        payload["attributes"] = attributes
    if observed_at:
        payload["observed_at"] = observed_at
    r = client.post(
        f"/api/v1/knowledge/entities/{entity_id}/observations",
        json=payload,
    )
    assert r.status_code == 201
    return r.json()["id"]


# ── Config Tests ─────────────────────────────────────────────────────────────

class TestGrowthConfig:
    def test_get_config(self):
        r = client.get("/api/v1/growth/config")
        assert r.status_code == 200
        data = r.json()
        assert "entity_types" in data
        assert "building" in data["entity_types"]
        assert "road" in data["entity_types"]
        assert "metrics" in data
        assert "length" in data["metrics"]
        assert "area" in data["metrics"]
        assert "forecast_algorithms" in data
        assert "linear_regression" in data["forecast_algorithms"]
        assert "change_statistics" in data
        assert "metric_units" in data


# ── Metric Calculation Tests ─────────────────────────────────────────────────

class TestMetricCalculation:
    def test_calculate_entity_metrics(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "Metric-BLD")
        add_observation(eid, {"count": 5, "area": 250.0}, "2024-01-15T00:00:00")
        add_observation(eid, {"count": 8, "area": 400.0}, "2024-06-15T00:00:00")

        r = client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["entity_id"] == eid
        assert data["metrics_computed"] >= 2

    def test_calculate_project_metrics(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "road", "Metric-RD")
        add_observation(eid, {"length": 500.0}, "2024-01-01T00:00:00")
        add_observation(eid, {"length": 750.0}, "2024-07-01T00:00:00")

        r = client.post("/api/v1/growth/calculate", json={
            "project_id": pid,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["project_id"] == pid
        assert data["entities_processed"] >= 1

    def test_get_metrics(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "Get-Metrics")
        add_observation(eid, {"count": 10}, "2024-01-01T00:00:00")
        client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })

        r = client.get(f"/api/v1/growth/metrics?project_id={pid}&entity_id={eid}")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1

    def test_growth_rate(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "Growth-Rate")
        add_observation(eid, {"count": 10}, "2024-01-01T00:00:00")
        add_observation(eid, {"count": 20}, "2025-01-01T00:00:00")
        client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })

        r = client.get(f"/api/v1/growth/metrics/growth-rate?entity_id={eid}&metric_name=count")
        assert r.status_code == 200
        data = r.json()
        assert data["annual_growth"] != 0
        assert data["observation_count"] >= 2

    def test_growth_rate_insufficient_data(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "No-Growth")
        add_observation(eid, {"count": 10}, "2024-01-01T00:00:00")
        client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })

        r = client.get(f"/api/v1/growth/metrics/growth-rate?entity_id={eid}&metric_name=count")
        assert r.status_code == 404

    def test_observation_frequency(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "Obs-Freq")
        add_observation(eid, {"count": 1}, "2024-01-01T00:00:00")
        add_observation(eid, {"count": 2}, "2024-06-01T00:00:00")
        add_observation(eid, {"count": 3}, "2025-01-01T00:00:00")

        r = client.get(f"/api/v1/growth/metrics/observation-frequency?entity_id={eid}")
        assert r.status_code == 200
        data = r.json()
        assert data["total_observations"] >= 2


# ── Temporal Analysis Tests ──────────────────────────────────────────────────

class TestTemporalAnalysis:
    def test_get_timeline(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "bridge", "Timeline-Bridge")
        add_observation(eid, {"count": 1}, "2024-01-01T00:00:00")

        r = client.get(f"/api/v1/growth/timeline?entity_id={eid}")
        assert r.status_code == 200
        data = r.json()
        assert data["entity_id"] == eid
        assert data["total_observations"] >= 1

    def test_growth_timeline(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "Growth-TL")
        add_observation(eid, {"count": 5}, "2024-01-01T00:00:00")
        add_observation(eid, {"count": 10}, "2024-06-01T00:00:00")
        client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })

        r = client.get(f"/api/v1/growth/timeline/growth?entity_id={eid}&metric_name=count")
        assert r.status_code == 200
        data = r.json()
        assert "data_points" in data
        assert data["entity_id"] == eid

    def test_expansion_timeline(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "settlement", "Expand-TL")
        add_observation(eid, {"area": 1000.0}, "2024-01-01T00:00:00")
        add_observation(eid, {"area": 1500.0}, "2024-06-01T00:00:00")
        client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })

        r = client.get(f"/api/v1/growth/timeline/expansion?entity_id={eid}")
        assert r.status_code == 200
        data = r.json()
        assert data["entity_id"] == eid

    def test_reduction_timeline(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "vegetation", "Reduce-TL")
        add_observation(eid, {"area": 5000.0}, "2024-01-01T00:00:00")
        add_observation(eid, {"area": 3000.0}, "2024-06-01T00:00:00")
        client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })

        r = client.get(f"/api/v1/growth/timeline/reduction?entity_id={eid}")
        assert r.status_code == 200
        data = r.json()
        assert data["total_reduction"] > 0

    def test_historical_timeline(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "Hist-TL")
        add_observation(eid, {"count": 10}, "2024-01-01T00:00:00")
        client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })

        r = client.get(f"/api/v1/growth/historical?project_id={pid}")
        assert r.status_code == 200
        data = r.json()
        assert data["project_id"] == pid


# ── Forecasting Tests ────────────────────────────────────────────────────────

class TestForecasting:
    def test_generate_forecast_linear(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "Forecast-Lin")
        for i in range(6):
            add_observation(
                eid, {"count": 10 + i * 5},
                f"2024-{(i+1)*2:02d}-01T00:00:00",
            )
        client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })

        r = client.post("/api/v1/growth/forecast", json={
            "project_id": pid,
            "entity_id": eid,
            "metric_name": "count",
            "algorithm": "linear_regression",
            "steps": 3,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["algorithm"] == "linear_regression"
        assert len(data["forecast"]) == 3
        assert "historical_fit_score" in data

    def test_generate_forecast_moving_average(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "Forecast-MA")
        for i in range(5):
            add_observation(
                eid, {"count": 20 + i * 2},
                f"2024-{(i+1)*2:02d}-01T00:00:00",
            )
        client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })

        r = client.post("/api/v1/growth/forecast", json={
            "project_id": pid,
            "entity_id": eid,
            "metric_name": "count",
            "algorithm": "moving_average",
            "steps": 2,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["algorithm"] == "moving_average"
        assert len(data["forecast"]) == 2

    def test_generate_forecast_polynomial(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "Forecast-Poly")
        for i in range(5):
            add_observation(
                eid, {"count": float(i ** 2 + 10)},
                f"2024-{(i+1)*2:02d}-01T00:00:00",
            )
        client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })

        r = client.post("/api/v1/growth/forecast", json={
            "project_id": pid,
            "entity_id": eid,
            "metric_name": "count",
            "algorithm": "polynomial_regression",
            "steps": 2,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["algorithm"] == "polynomial_regression"

    def test_generate_forecast_exponential(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "Forecast-Exp")
        for i in range(5):
            add_observation(
                eid, {"count": float(10 * (1.5 ** i))},
                f"2024-{(i+1)*2:02d}-01T00:00:00",
            )
        client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })

        r = client.post("/api/v1/growth/forecast", json={
            "project_id": pid,
            "entity_id": eid,
            "metric_name": "count",
            "algorithm": "exponential_trend",
            "steps": 3,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["algorithm"] == "exponential_trend"

    def test_forecast_insufficient_data(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "Forecast-Short")
        add_observation(eid, {"count": 10}, "2024-01-01T00:00:00")
        client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })

        r = client.post("/api/v1/growth/forecast", json={
            "project_id": pid,
            "entity_id": eid,
            "metric_name": "count",
            "algorithm": "linear_regression",
        })
        assert r.status_code == 400

    def test_get_forecasts(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "Get-Forecasts")
        for i in range(4):
            add_observation(
                eid, {"count": 10 + i * 3},
                f"2024-{(i+1)*3:02d}-01T00:00:00",
            )
        client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })
        client.post("/api/v1/growth/forecast", json={
            "project_id": pid,
            "entity_id": eid,
            "metric_name": "count",
            "steps": 3,
        })

        r = client.get(f"/api/v1/growth/forecast?project_id={pid}")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 3

    def test_get_forecast_models(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "Forecast-Models")
        for i in range(4):
            add_observation(
                eid, {"count": 10 + i},
                f"2024-{(i+1)*3:02d}-01T00:00:00",
            )
        client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })
        client.post("/api/v1/growth/forecast", json={
            "project_id": pid,
            "entity_id": eid,
            "metric_name": "count",
            "steps": 2,
        })

        r = client.get(f"/api/v1/growth/forecast/models?project_id={pid}")
        assert r.status_code == 200
        data = r.json()
        assert len(data["items"]) >= 1


# ── Hotspot Detection Tests ─────────────────────────────────────────────────

class TestHotspotDetection:
    def test_detect_hotspots(self):
        pid = get_test_project()
        for i in range(3):
            eid = create_test_entity(pid, "building", f"Hotspot-{i}")
            add_observation(eid, {"count": 10}, "2024-01-01T00:00:00")
            add_observation(eid, {"count": 10 + i * 20}, "2025-01-01T00:00:00")
            client.post("/api/v1/growth/calculate", json={
                "project_id": pid, "entity_id": eid,
            })

        r = client.post("/api/v1/growth/hotspots", json={
            "project_id": pid,
            "metric_name": "count",
            "threshold": 1.0,
        })
        assert r.status_code == 200
        data = r.json()
        assert "hotspots" in data
        assert data["total_entities_analyzed"] >= 3

    def test_detect_hotspots_by_type(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "road", "Hotspot-RD")
        add_observation(eid, {"length": 100}, "2024-01-01T00:00:00")
        add_observation(eid, {"length": 300}, "2025-01-01T00:00:00")
        client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })

        r = client.post("/api/v1/growth/hotspots", json={
            "project_id": pid,
            "metric_name": "length",
            "threshold": 0.5,
            "entity_type": "road",
        })
        assert r.status_code == 200


# ── Change Statistics Tests ─────────────────────────────────────────────────

class TestChangeStatistics:
    def test_calculate_change_statistics(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "road", "Change-RD")
        add_observation(eid, {"length": 1000}, "2024-01-01T00:00:00")
        add_observation(eid, {"length": 1500}, "2025-01-01T00:00:00")
        client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })

        r = client.post(f"/api/v1/growth/change-statistics?project_id={pid}")
        assert r.status_code == 200
        data = r.json()
        assert "statistics" in data
        assert "road_added" in data["statistics"]

    def test_get_change_statistics_history(self):
        pid = get_test_project()
        r = client.get(f"/api/v1/growth/change-statistics?project_id={pid}")
        assert r.status_code == 200
        assert "items" in r.json()


# ── History Tests ────────────────────────────────────────────────────────────

class TestGrowthHistory:
    def test_get_growth_history(self):
        pid = get_test_project()
        r = client.get(f"/api/v1/growth/history?project_id={pid}")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data


# ── Forecast Uncertainty Tests ───────────────────────────────────────────────

class TestForecastUncertainty:
    def test_forecast_has_uncertainty(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "Uncertainty")
        for i in range(5):
            add_observation(
                eid, {"count": 10 + i * 4},
                f"2024-{(i+1)*2:02d}-01T00:00:00",
            )
        client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })

        r = client.post("/api/v1/growth/forecast", json={
            "project_id": pid,
            "entity_id": eid,
            "metric_name": "count",
            "steps": 3,
        })
        assert r.status_code == 200
        data = r.json()
        for f in data["forecast"]:
            assert f["confidence_interval_lower"] <= f["predicted_value"]
            assert f["predicted_value"] <= f["confidence_interval_upper"]
            assert f["prediction_range_lower"] <= f["predicted_value"]
            assert f["predicted_value"] <= f["prediction_range_upper"]
            assert f["confidence_level"] == 0.95
            assert f["algorithm"] != ""

    def test_forecast_all_algorithms_have_uncertainty(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "All-Algos")
        for i in range(5):
            add_observation(
                eid, {"count": float(10 * (1.3 ** i))},
                f"2024-{(i+1)*2:02d}-01T00:00:00",
            )
        client.post("/api/v1/growth/calculate", json={
            "project_id": pid, "entity_id": eid,
        })

        for algo in ["linear_regression", "moving_average", "polynomial_regression", "exponential_trend"]:
            r = client.post("/api/v1/growth/forecast", json={
                "project_id": pid,
                "entity_id": eid,
                "metric_name": "count",
                "algorithm": algo,
                "steps": 2,
            })
            assert r.status_code == 200, f"Algorithm {algo} failed"
            data = r.json()
            for f in data["forecast"]:
                assert f["confidence_interval_lower"] <= f["predicted_value"]
                assert f["predicted_value"] <= f["confidence_interval_upper"]
