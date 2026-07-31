"""Tests for the Intelligence Query Engine."""

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def get_test_project() -> str:
    """Create a test project and return its ID."""
    unique_name = f"Query Test {uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/projects",
        json={
            "name": unique_name,
            "description": "Query engine test project",
        },
    )
    assert r.status_code == 201
    return r.json()["id"]


def create_test_entity(project_id: str, entity_type: str = "building", name: str | None = None) -> str:
    """Create a test entity and return its ID."""
    if name is None:
        name = f"TST-{uuid.uuid4().hex[:6]}"
    r = client.post(
        f"/api/v1/knowledge/project/{project_id}/entities",
        json={"entity_type": entity_type, "name": name},
    )
    assert r.status_code == 201
    return r.json()["id"]


# ── Config Tests ─────────────────────────────────────────────────────────────

class TestQueryConfig:
    def test_get_config(self):
        r = client.get("/api/v1/queries/config")
        assert r.status_code == 200
        data = r.json()
        assert "entity_types" in data
        assert "building" in data["entity_types"]
        assert "spatial_operators" in data
        assert "bbox" in data["spatial_operators"]
        assert "temporal_operators" in data
        assert "before" in data["temporal_operators"]
        assert "export_formats" in data
        assert "csv" in data["export_formats"]


# ── Query Execution Tests ────────────────────────────────────────────────────

class TestQueryExecution:
    def test_execute_query_empty(self):
        pid = get_test_project()
        r = client.post("/api/v1/queries/execute", json={
            "project_id": pid,
            "page": 0,
            "page_size": 50,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_execute_query_with_entities(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "Query-Test-BLD")

        r = client.post("/api/v1/queries/execute", json={
            "project_id": pid,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1
        assert any(item["id"] == eid for item in data["items"])

    def test_execute_query_by_entity_type(self):
        pid = get_test_project()
        create_test_entity(pid, "building", "BLD-Query-A")
        create_test_entity(pid, "road", "RD-Query-A")

        r = client.post("/api/v1/queries/execute", json={
            "project_id": pid,
            "entity_types": ["road"],
        })
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert data["items"][0]["entity_type"] == "road"

    def test_execute_query_by_name(self):
        pid = get_test_project()
        create_test_entity(pid, "building", "Searchable-Building")

        r = client.post("/api/v1/queries/execute", json={
            "project_id": pid,
            "entity_name": "Searchable",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1

    def test_execute_query_by_confidence(self):
        pid = get_test_project()
        r1 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "HighConf", "confidence": 0.95},
        )
        r2 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "road", "name": "LowConf", "confidence": 0.3},
        )
        assert r1.status_code == 201
        assert r2.status_code == 201

        r = client.post("/api/v1/queries/execute", json={
            "project_id": pid,
            "confidence_min": 0.8,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1
        names = [item["name"] for item in data["items"]]
        assert "HighConf" in names

    def test_execute_query_pagination(self):
        pid = get_test_project()
        for i in range(5):
            create_test_entity(pid, "building", f"PAG-{i}")

        r = client.post("/api/v1/queries/execute", json={
            "project_id": pid,
            "page": 0,
            "page_size": 2,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 5
        assert len(data["items"]) == 2

    def test_execute_raw_query(self):
        pid = get_test_project()
        create_test_entity(pid, "bridge", "Raw-Bridge")

        r = client.post(
            f"/api/v1/queries/execute/raw?project_id={pid}",
            json={"entity_types": ["bridge"]},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1
        assert data["items"][0]["entity_type"] == "bridge"


# ── Saved Queries Tests ──────────────────────────────────────────────────────

class TestSavedQueries:
    def test_save_query(self):
        pid = get_test_project()
        r = client.post("/api/v1/queries/saved", json={
            "project_id": pid,
            "name": "My Test Query",
            "filters_json": json.dumps({"entity_types": ["building"]}),
        })
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "My Test Query"
        assert data["project_id"] == pid

    def test_list_saved_queries(self):
        pid = get_test_project()
        client.post("/api/v1/queries/saved", json={
            "project_id": pid,
            "name": "Q1",
            "filters_json": "{}",
        })
        client.post("/api/v1/queries/saved", json={
            "project_id": pid,
            "name": "Q2",
            "filters_json": "{}",
        })
        r = client.get(f"/api/v1/queries/saved?project_id={pid}")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2

    def test_get_saved_query(self):
        pid = get_test_project()
        r = client.post("/api/v1/queries/saved", json={
            "project_id": pid,
            "name": "Get Me",
            "filters_json": json.dumps({"entity_types": ["road"]}),
        })
        qid = r.json()["id"]

        r = client.get(f"/api/v1/queries/saved/{qid}")
        assert r.status_code == 200
        assert r.json()["name"] == "Get Me"

    def test_get_saved_query_not_found(self):
        r = client.get(f"/api/v1/queries/saved/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_update_saved_query(self):
        pid = get_test_project()
        r = client.post("/api/v1/queries/saved", json={
            "project_id": pid,
            "name": "Original",
            "filters_json": "{}",
        })
        qid = r.json()["id"]

        r = client.put(f"/api/v1/queries/saved/{qid}", json={
            "name": "Updated",
            "favorite": True,
        })
        assert r.status_code == 200
        assert r.json()["name"] == "Updated"
        assert r.json()["favorite"] is True

    def test_delete_saved_query(self):
        pid = get_test_project()
        r = client.post("/api/v1/queries/saved", json={
            "project_id": pid,
            "name": "Delete Me",
            "filters_json": "{}",
        })
        qid = r.json()["id"]

        r = client.delete(f"/api/v1/queries/saved/{qid}")
        assert r.status_code == 204

        r = client.get(f"/api/v1/queries/saved/{qid}")
        assert r.status_code == 404

    def test_toggle_favorite(self):
        pid = get_test_project()
        r = client.post("/api/v1/queries/saved", json={
            "project_id": pid,
            "name": "Fav Test",
            "filters_json": "{}",
        })
        qid = r.json()["id"]
        assert r.json()["favorite"] is False

        r = client.post(f"/api/v1/queries/saved/{qid}/favorite")
        assert r.status_code == 200
        assert r.json()["favorite"] is True

    def test_toggle_pinned(self):
        pid = get_test_project()
        r = client.post("/api/v1/queries/saved", json={
            "project_id": pid,
            "name": "Pin Test",
            "filters_json": "{}",
        })
        qid = r.json()["id"]
        assert r.json()["pinned"] is False

        r = client.post(f"/api/v1/queries/saved/{qid}/pin")
        assert r.status_code == 200
        assert r.json()["pinned"] is True

    def test_rerun_saved_query(self):
        pid = get_test_project()
        create_test_entity(pid, "building", "Rerun-Me")
        r = client.post("/api/v1/queries/saved", json={
            "project_id": pid,
            "name": "Rerun Test",
            "filters_json": json.dumps({"entity_types": ["building"]}),
        })
        qid = r.json()["id"]

        r = client.post(f"/api/v1/queries/saved/{qid}/rerun")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1


# ── Query History Tests ──────────────────────────────────────────────────────

class TestQueryHistory:
    def test_execute_records_history(self):
        pid = get_test_project()
        client.post("/api/v1/queries/execute", json={
            "project_id": pid,
        })

        r = client.get(f"/api/v1/queries/history?project_id={pid}")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1

    def test_list_history(self):
        pid = get_test_project()
        client.post("/api/v1/queries/execute", json={"project_id": pid})
        client.post("/api/v1/queries/execute", json={"project_id": pid})

        r = client.get(f"/api/v1/queries/history?project_id={pid}")
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_delete_history_entry(self):
        pid = get_test_project()
        client.post("/api/v1/queries/execute", json={"project_id": pid})
        r = client.get(f"/api/v1/queries/history?project_id={pid}")
        hid = r.json()["items"][0]["id"]

        r = client.delete(f"/api/v1/queries/history/{hid}")
        assert r.status_code == 204

    def test_clear_history(self):
        pid = get_test_project()
        client.post("/api/v1/queries/execute", json={"project_id": pid})

        r = client.delete(f"/api/v1/queries/history?project_id={pid}")
        assert r.status_code == 204

        r = client.get(f"/api/v1/queries/history?project_id={pid}")
        assert r.json()["total"] == 0


# ── Export Tests ─────────────────────────────────────────────────────────────

class TestExport:
    def test_export_csv(self):
        pid = get_test_project()
        create_test_entity(pid, "building", "Export-Me")

        r = client.post("/api/v1/queries/export", json={
            "project_id": pid,
            "format": "csv",
            "filters": {},
        })
        assert r.status_code == 200
        data = r.json()
        assert data["format"] == "csv"
        assert data["count"] >= 1
        assert "Export-Me" in data["content"]

    def test_export_geojson(self):
        pid = get_test_project()
        create_test_entity(pid, "building", "GeoJSON-Test")

        r = client.post("/api/v1/queries/export", json={
            "project_id": pid,
            "format": "geojson",
            "filters": {},
        })
        assert r.status_code == 200
        data = r.json()
        assert data["format"] == "geojson"
        assert '"type": "FeatureCollection"' in data["content"]

    def test_export_kml(self):
        pid = get_test_project()
        create_test_entity(pid, "road", "KML-Test")

        r = client.post("/api/v1/queries/export", json={
            "project_id": pid,
            "format": "kml",
            "filters": {},
        })
        assert r.status_code == 200
        data = r.json()
        assert data["format"] == "kml"
        assert "<kml" in data["content"]

    def test_export_invalid_format(self):
        pid = get_test_project()
        r = client.post("/api/v1/queries/export", json={
            "project_id": pid,
            "format": "invalid",
            "filters": {},
        })
        assert r.status_code == 400

    def test_export_no_results(self):
        pid = get_test_project()
        r = client.post("/api/v1/queries/export", json={
            "project_id": pid,
            "format": "csv",
            "filters": {"entity_types": ["nonexistent_type"]},
        })
        assert r.status_code == 404


# ── Spatial Filter Tests ─────────────────────────────────────────────────────

class TestSpatialFilters:
    def test_filter_by_bbox(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={
                "entity_type": "building",
                "name": "Bbox-Test",
                "bbox": [1.0, 2.0, 3.0, 4.0],
                "centroid": [2.0, 3.0],
            },
        )
        assert r.status_code == 201

        r = client.post("/api/v1/queries/execute", json={
            "project_id": pid,
            "spatial": {
                "operator": "bbox",
                "bbox": [0.0, 0.0, 5.0, 5.0],
            },
        })
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1


# ── Temporal Filter Tests ────────────────────────────────────────────────────

class TestTemporalFilters:
    def test_filter_by_created_after(self):
        pid = get_test_project()
        create_test_entity(pid, "bridge", "Temporal-Test")

        r = client.post("/api/v1/queries/execute", json={
            "project_id": pid,
            "temporal": {
                "operator": "after",
                "date": "2020-01-01T00:00:00",
            },
        })
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1


# ── Cache Tests ──────────────────────────────────────────────────────────────

class TestQueryCache:
    def test_clear_cache(self):
        r = client.delete("/api/v1/queries/cache")
        assert r.status_code == 204


# ── Entity Type Filter Tests ─────────────────────────────────────────────────

class TestEntityTypeFilters:
    def test_all_entity_types(self):
        pid = get_test_project()
        entity_types = [
            "road", "bridge", "building", "settlement", "river",
            "vegetation", "airfield", "tunnel", "railway", "port", "unknown",
        ]
        for etype in entity_types:
            create_test_entity(pid, etype, f"TypeTest-{etype}")

        for etype in entity_types:
            r = client.post("/api/v1/queries/execute", json={
                "project_id": pid,
                "entity_types": [etype],
            })
            assert r.status_code == 200
            assert r.json()["total"] >= 1, f"Failed for type: {etype}"
