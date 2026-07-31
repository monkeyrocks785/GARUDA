"""Tests for Mission Engine."""

import uuid

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def get_test_project() -> str:
    """Create a test project and return its ID."""
    response = client.post(
        "/api/v1/projects",
        json={"name": f"Mission Test Project {uuid.uuid4().hex[:8]}"},
    )
    assert response.status_code in (200, 201), f"Failed to create project: {response.status_code} {response.text}"
    return response.json()["id"]


def test_create_mission():
    r = client.post("/api/v1/missions", json={
        "name": f"Test Mission {uuid.uuid4().hex[:8]}",
        "code": "TM-001",
        "description": "A test mission",
        "status": "planning",
        "priority": "high",
        "tags": ["test", "demo"],
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"].startswith("Test Mission")
    assert data["status"] == "planning"
    assert data["priority"] == "high"


def test_list_missions():
    client.post("/api/v1/missions", json={"name": f"List Mission {uuid.uuid4().hex[:8]}"})
    client.post("/api/v1/missions", json={"name": f"List Mission 2 {uuid.uuid4().hex[:8]}"})
    r = client.get("/api/v1/missions")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 2


def test_get_mission():
    r = client.post("/api/v1/missions", json={"name": f"Get Mission {uuid.uuid4().hex[:8]}"})
    mid = r.json()["id"]
    r = client.get(f"/api/v1/missions/{mid}")
    assert r.status_code == 200
    assert r.json()["id"] == mid


def test_get_mission_not_found():
    r = client.get("/api/v1/missions/nonexistent")
    assert r.status_code == 404


def test_update_mission():
    r = client.post("/api/v1/missions", json={"name": f"Update Mission {uuid.uuid4().hex[:8]}"})
    mid = r.json()["id"]
    r = client.put(f"/api/v1/missions/{mid}", json={"name": "Updated Mission", "priority": "critical"})
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Mission"
    assert r.json()["priority"] == "critical"


def test_delete_mission():
    r = client.post("/api/v1/missions", json={"name": f"Delete Mission {uuid.uuid4().hex[:8]}"})
    mid = r.json()["id"]
    r = client.delete(f"/api/v1/missions/{mid}")
    assert r.status_code == 200
    r = client.get(f"/api/v1/missions/{mid}")
    assert r.status_code == 404


def test_archive_mission():
    r = client.post("/api/v1/missions", json={"name": f"Archive Mission {uuid.uuid4().hex[:8]}"})
    mid = r.json()["id"]
    r = client.post(f"/api/v1/missions/{mid}/archive")
    assert r.status_code == 200
    assert r.json()["archived"] == True
    assert r.json()["status"] == "archived"


def test_toggle_favorite():
    r = client.post("/api/v1/missions", json={"name": f"Fav Mission {uuid.uuid4().hex[:8]}"})
    mid = r.json()["id"]
    r = client.post(f"/api/v1/missions/{mid}/favorite")
    assert r.status_code == 200
    assert r.json()["favorite"] == True
    r = client.post(f"/api/v1/missions/{mid}/favorite")
    assert r.json()["favorite"] == False


def test_add_project():
    mid = client.post("/api/v1/missions", json={"name": f"Link Mission {uuid.uuid4().hex[:8]}"}).json()["id"]
    pid = get_test_project()
    r = client.post(f"/api/v1/missions/{mid}/project", json={"project_id": pid})
    assert r.status_code == 200
    assert r.json()["status"] == "linked"


def test_get_mission_projects():
    mid = client.post("/api/v1/missions", json={"name": f"Projects Mission {uuid.uuid4().hex[:8]}"}).json()["id"]
    pid = get_test_project()
    client.post(f"/api/v1/missions/{mid}/project", json={"project_id": pid})
    r = client.get(f"/api/v1/missions/{mid}/projects")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_remove_project():
    mid = client.post("/api/v1/missions", json={"name": f"Unlink Mission {uuid.uuid4().hex[:8]}"}).json()["id"]
    pid = get_test_project()
    client.post(f"/api/v1/missions/{mid}/project", json={"project_id": pid})
    r = client.delete(f"/api/v1/missions/{mid}/project/{pid}")
    assert r.status_code == 200


def test_get_timeline():
    r = client.post("/api/v1/missions", json={"name": f"Timeline Mission {uuid.uuid4().hex[:8]}"})
    mid = r.json()["id"]
    r = client.get(f"/api/v1/missions/{mid}/timeline")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_add_note():
    mid = client.post("/api/v1/missions", json={"name": f"Notes Mission {uuid.uuid4().hex[:8]}"}).json()["id"]
    r = client.post(f"/api/v1/missions/{mid}/notes", json={"title": "Test Note", "content": "Note content"})
    assert r.status_code == 201
    assert r.json()["title"] == "Test Note"


def test_get_notes():
    mid = client.post("/api/v1/missions", json={"name": f"Get Notes Mission {uuid.uuid4().hex[:8]}"}).json()["id"]
    client.post(f"/api/v1/missions/{mid}/notes", json={"title": "Note 1"})
    client.post(f"/api/v1/missions/{mid}/notes", json={"title": "Note 2"})
    r = client.get(f"/api/v1/missions/{mid}/notes")
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_search_missions():
    name = f"Searchable {uuid.uuid4().hex[:8]}"
    client.post("/api/v1/missions", json={"name": name})
    r = client.get(f"/api/v1/missions?search={name[:20]}")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_filter_by_status():
    client.post("/api/v1/missions", json={"name": f"Active {uuid.uuid4().hex[:8]}", "status": "active"})
    r = client.get("/api/v1/missions?status=active")
    assert r.status_code == 200


def test_filter_by_priority():
    client.post("/api/v1/missions", json={"name": f"Critical {uuid.uuid4().hex[:8]}", "priority": "critical"})
    r = client.get("/api/v1/missions?priority=critical")
    assert r.status_code == 200


def test_mission_stats():
    r = client.get("/api/v1/missions/stats")
    assert r.status_code == 200
    stats = r.json()
    assert "total" in stats
    assert "active" in stats
