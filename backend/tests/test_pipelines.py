"""Tests for Pipeline Engine."""

import uuid

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def get_test_project() -> str:
    """Create a test project and return its ID."""
    response = client.post(
        "/api/v1/projects",
        json={"name": f"Pipeline Test {uuid.uuid4().hex[:8]}"},
    )
    assert response.status_code in (200, 201), f"Failed to create project: {response.status_code} {response.text}"
    return response.json()["id"]


def test_create_pipeline():
    pid = get_test_project()
    r = client.post("/api/v1/pipelines/", json={
        "name": "Test Pipeline",
        "description": "A test",
        "project_id": pid,
        "nodes": [
            {"name": "Import", "node_type": "import_file"},
            {"name": "Validate", "node_type": "validate"},
        ],
    })
    assert r.status_code in (200, 201), f"Create failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["status"] == "pending"
    assert data["total_nodes"] == 2


def test_list_pipelines():
    pid = get_test_project()
    client.post("/api/v1/pipelines/", json={
        "name": "Pipeline 1",
        "project_id": pid,
        "nodes": [{"name": "A", "node_type": "custom"}],
    })
    client.post("/api/v1/pipelines/", json={
        "name": "Pipeline 2",
        "nodes": [{"name": "B", "node_type": "custom"}],
    })
    r = client.get("/api/v1/pipelines/")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 2


def test_start_pipeline():
    pid = get_test_project()
    r = client.post("/api/v1/pipelines/", json={
        "name": "Start Test",
        "project_id": pid,
        "nodes": [{"name": "A", "node_type": "custom"}],
    })
    pipeline_id = r.json()["id"]
    r = client.post(f"/api/v1/pipelines/{pipeline_id}/start")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


def test_cancel_pipeline():
    pid = get_test_project()
    r = client.post("/api/v1/pipelines/", json={
        "name": "Cancel Test",
        "project_id": pid,
        "nodes": [{"name": "A", "node_type": "custom"}],
    })
    pipeline_id = r.json()["id"]
    r = client.post(f"/api/v1/pipelines/{pipeline_id}/cancel")
    assert r.status_code == 400


def test_retry_pipeline():
    pid = get_test_project()
    r = client.post("/api/v1/pipelines/", json={
        "name": "Retry Test",
        "project_id": pid,
        "nodes": [{"name": "A", "node_type": "custom"}],
    })
    pipeline_id = r.json()["id"]
    r = client.post(f"/api/v1/pipelines/{pipeline_id}/retry")
    assert r.status_code == 400


def test_delete_pipeline():
    pid = get_test_project()
    r = client.post("/api/v1/pipelines/", json={
        "name": "Delete Test",
        "project_id": pid,
        "nodes": [{"name": "A", "node_type": "custom"}],
    })
    pipeline_id = r.json()["id"]
    r = client.delete(f"/api/v1/pipelines/{pipeline_id}")
    assert r.status_code == 200
    r = client.get(f"/api/v1/pipelines/{pipeline_id}")
    assert r.status_code == 404


def test_get_pipeline_nodes():
    pid = get_test_project()
    r = client.post("/api/v1/pipelines/", json={
        "name": "Nodes Test",
        "project_id": pid,
        "nodes": [
            {"name": "Import", "node_type": "import_file"},
            {"name": "Validate", "node_type": "validate"},
        ],
    })
    pipeline_id = r.json()["id"]
    r = client.get(f"/api/v1/pipelines/{pipeline_id}/nodes")
    assert r.status_code == 200
    nodes = r.json()
    assert len(nodes) == 2


def test_get_pipeline_history():
    pid = get_test_project()
    r = client.post("/api/v1/pipelines/", json={
        "name": "History Test",
        "project_id": pid,
        "nodes": [{"name": "A", "node_type": "custom"}],
    })
    pipeline_id = r.json()["id"]
    client.post(f"/api/v1/pipelines/{pipeline_id}/start")
    r = client.get(f"/api/v1/pipelines/{pipeline_id}/history")
    assert r.status_code == 200


def test_get_pipeline_logs():
    pid = get_test_project()
    r = client.post("/api/v1/pipelines/", json={
        "name": "Logs Test",
        "project_id": pid,
        "nodes": [{"name": "A", "node_type": "custom"}],
    })
    pipeline_id = r.json()["id"]
    client.post(f"/api/v1/pipelines/{pipeline_id}/start")
    r = client.get(f"/api/v1/pipelines/{pipeline_id}/logs")
    assert r.status_code == 200


def test_get_node_types():
    r = client.get("/api/v1/pipelines/node-types")
    assert r.status_code == 200
    types = r.json()
    assert len(types) >= 6
    type_names = [t["type"] for t in types]
    assert "import_file" in type_names
    assert "validate" in type_names


def test_get_pipeline_stats():
    r = client.get("/api/v1/pipelines/stats")
    assert r.status_code == 200
    stats = r.json()
    assert "total" in stats


def test_enqueue_dequeue():
    pid = get_test_project()
    r = client.post("/api/v1/pipelines/", json={
        "name": "Queue Test",
        "project_id": pid,
        "nodes": [{"name": "A", "node_type": "custom"}],
    })
    pipeline_id = r.json()["id"]
    r = client.post(f"/api/v1/pipelines/{pipeline_id}/enqueue", json={"priority": 5})
    assert r.status_code == 200
    r = client.get("/api/v1/pipelines/queue/status")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_pause_resume():
    pid = get_test_project()
    r = client.post("/api/v1/pipelines/", json={
        "name": "Pause Test",
        "project_id": pid,
        "nodes": [{"name": "A", "node_type": "custom"}],
    })
    pipeline_id = r.json()["id"]
    r = client.post(f"/api/v1/pipelines/{pipeline_id}/pause")
    assert r.status_code == 400
