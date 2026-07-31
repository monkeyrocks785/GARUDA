"""Tests for Project management endpoints."""

import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from database.connection import Base, engine
from main import app

# Create tables for testing
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_create_project():
    """Test creating a new project."""
    import uuid
    unique_name = f"Test Project {uuid.uuid4().hex[:8]}"

    response = client.post(
        "/api/v1/projects",
        json={
            "name": unique_name,
            "description": "A test project",
            "area_of_interest": "Test Area",
            "tags": ["test", "demo"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == unique_name
    assert data["description"] == "A test project"
    assert data["status"] == "created"
    assert data["favorite"] == False
    assert data["archived"] == False

    # Verify storage was created
    storage_path = Path(data["storage_path"])
    assert storage_path.exists()
    assert (storage_path / "imagery").exists()
    assert (storage_path / "vectors").exists()
    assert (storage_path / "metadata" / "project.json").exists()

    # Cleanup
    shutil.rmtree(storage_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{data['id']}")


def test_create_project_validation():
    """Test project name validation."""
    # Empty name - Pydantic returns 422 for validation errors
    response = client.post("/api/v1/projects", json={"name": ""})
    assert response.status_code == 422

    # Duplicate name
    response1 = client.post("/api/v1/projects", json={"name": "Duplicate Test"})
    assert response1.status_code == 201
    project_id = response1.json()["id"]

    response2 = client.post("/api/v1/projects", json={"name": "Duplicate Test"})
    assert response2.status_code == 400

    # Cleanup
    storage_path = Path(response1.json()["storage_path"])
    shutil.rmtree(storage_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{project_id}")


def test_list_projects():
    """Test listing projects."""
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert "total" in data


def test_get_project():
    """Test getting a project by ID."""
    # Create a project first
    create_response = client.post(
        "/api/v1/projects",
        json={"name": "Get Test Project"},
    )
    project_id = create_response.json()["id"]

    # Get the project
    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Get Test Project"

    # Cleanup
    storage_path = Path(create_response.json()["storage_path"])
    shutil.rmtree(storage_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{project_id}")


def test_get_project_not_found():
    """Test getting a non-existent project."""
    response = client.get("/api/v1/projects/nonexistent-id")
    assert response.status_code == 404


def test_update_project():
    """Test updating a project."""
    # Create a project
    create_response = client.post(
        "/api/v1/projects",
        json={"name": "Update Test Project"},
    )
    project_id = create_response.json()["id"]

    # Update the project
    response = client.put(
        f"/api/v1/projects/{project_id}",
        json={"name": "Updated Project Name", "description": "Updated description"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Project Name"
    assert response.json()["description"] == "Updated description"

    # Cleanup
    storage_path = Path(create_response.json()["storage_path"])
    shutil.rmtree(storage_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{project_id}")


def test_delete_project():
    """Test deleting a project."""
    # Create a project
    create_response = client.post(
        "/api/v1/projects",
        json={"name": "Delete Test Project"},
    )
    project_id = create_response.json()["id"]
    storage_path = Path(create_response.json()["storage_path"])

    # Delete the project
    response = client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 204

    # Verify project is deleted
    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 404

    # Verify storage is deleted
    assert not storage_path.exists()


def test_duplicate_project():
    """Test duplicating a project."""
    # Create original project
    create_response = client.post(
        "/api/v1/projects",
        json={"name": "Original Project", "description": "Original description"},
    )
    original_id = create_response.json()["id"]

    # Duplicate the project
    response = client.post(f"/api/v1/projects/{original_id}/duplicate")
    assert response.status_code == 201
    assert response.json()["name"] == "Original Project (Copy)"

    # Verify duplicate has its own storage
    duplicate_path = Path(response.json()["storage_path"])
    assert duplicate_path.exists()

    # Cleanup
    original_path = Path(create_response.json()["storage_path"])
    shutil.rmtree(original_path, ignore_errors=True)
    shutil.rmtree(duplicate_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{original_id}")
    client.delete(f"/api/v1/projects/{response.json()['id']}")


def test_archive_project():
    """Test archiving a project."""
    # Create a project
    create_response = client.post(
        "/api/v1/projects",
        json={"name": "Archive Test Project"},
    )
    project_id = create_response.json()["id"]

    # Archive the project
    response = client.post(f"/api/v1/projects/{project_id}/archive")
    assert response.status_code == 200
    assert response.json()["archived"] == True
    assert response.json()["status"] == "archived"

    # Cleanup
    storage_path = Path(create_response.json()["storage_path"])
    shutil.rmtree(storage_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{project_id}")


def test_toggle_favorite():
    """Test toggling favorite status."""
    # Create a project
    create_response = client.post(
        "/api/v1/projects",
        json={"name": "Favorite Test Project"},
    )
    project_id = create_response.json()["id"]

    # Toggle favorite on
    response = client.post(f"/api/v1/projects/{project_id}/favorite")
    assert response.status_code == 200
    assert response.json()["favorite"] == True

    # Toggle favorite off
    response = client.post(f"/api/v1/projects/{project_id}/favorite")
    assert response.status_code == 200
    assert response.json()["favorite"] == False

    # Cleanup
    storage_path = Path(create_response.json()["storage_path"])
    shutil.rmtree(storage_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{project_id}")


def test_search_projects():
    """Test searching projects."""
    # Create a project with unique name
    create_response = client.post(
        "/api/v1/projects",
        json={"name": "Searchable Project XYZ"},
    )
    project_id = create_response.json()["id"]

    # Search for it
    response = client.get("/api/v1/projects?search=Searchable")
    assert response.status_code == 200
    assert response.json()["total"] >= 1

    # Cleanup
    storage_path = Path(create_response.json()["storage_path"])
    shutil.rmtree(storage_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{project_id}")


def test_recovery_check():
    """Test recovery endpoint."""
    response = client.get("/api/v1/projects/recovery")
    assert response.status_code == 200
    assert "recovered" in response.json()
    assert "count" in response.json()


def test_get_project_response_has_all_fields():
    """Test that project response includes all fields the frontend expects."""
    create_response = client.post(
        "/api/v1/projects",
        json={"name": f"Field Check {__import__('uuid').uuid4().hex[:8]}"},
    )
    project_id = create_response.json()["id"]
    storage_path = Path(create_response.json()["storage_path"])

    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()

    # Verify all frontend-expected fields are present
    assert "id" in data
    assert "name" in data
    assert "description" in data
    assert "status" in data
    assert "current_stage" in data
    assert "current_task" in data
    assert "progress" in data
    assert "area_of_interest" in data
    assert "coordinate_system" in data
    assert "storage_path" in data
    assert "tags" in data
    assert "notes" in data
    assert "favorite" in data
    assert "archived" in data
    assert "completed_steps" in data
    assert "pending_steps" in data
    assert "last_opened_file" in data
    assert "last_viewed_map_position" in data
    assert "selected_layers" in data
    assert "dashboard_layout" in data
    assert "user_notes" in data
    assert "is_processing" in data
    assert "last_job_id" in data
    assert "last_job_status" in data
    assert "project_version" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "last_opened_at" in data

    # Verify defaults
    assert data["status"] == "created"
    assert data["favorite"] is False
    assert data["archived"] is False
    assert data["is_processing"] is False
    assert data["progress"] == 0.0
    assert data["project_version"] == "1.0.0"

    shutil.rmtree(storage_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{project_id}")


def test_project_not_found_returns_404():
    """Test that accessing a non-existent project returns 404."""
    response = client.get("/api/v1/projects/nonexistent-id-12345")
    assert response.status_code == 404


def test_project_list_response_has_all_fields():
    """Test that project list response includes all fields."""
    create_response = client.post(
        "/api/v1/projects",
        json={"name": f"List Field Check {__import__('uuid').uuid4().hex[:8]}"},
    )
    project_id = create_response.json()["id"]
    storage_path = Path(create_response.json()["storage_path"])

    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()

    assert "projects" in data
    assert "total" in data
    assert data["total"] >= 1

    # Check first project has all fields
    first_project = data["projects"][0]
    assert "id" in first_project
    assert "name" in first_project
    assert "completed_steps" in first_project
    assert "pending_steps" in first_project
    assert "last_opened_file" in first_project
    assert "last_viewed_map_position" in first_project
    assert "selected_layers" in first_project
    assert "dashboard_layout" in first_project
    assert "user_notes" in first_project
    assert "is_processing" in first_project
    assert "last_job_id" in first_project
    assert "last_job_status" in first_project

    shutil.rmtree(storage_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{project_id}")


def test_project_update_last_opened():
    """Test that project tracks last_opened_at correctly."""
    create_response = client.post(
        "/api/v1/projects",
        json={"name": f"Last Opened Test {__import__('uuid').uuid4().hex[:8]}"},
    )
    project_id = create_response.json()["id"]
    storage_path = Path(create_response.json()["storage_path"])

    # Initially last_opened_at should be null
    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["last_opened_at"] is None

    # Update last_opened_at via PUT with ISO format
    response = client.put(
        f"/api/v1/projects/{project_id}",
        json={"name": create_response.json()["name"], "last_opened_at": "2025-01-15T10:30:00.000Z"},
    )
    assert response.status_code == 200

    # Verify it persisted
    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["last_opened_at"] is not None

    shutil.rmtree(storage_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{project_id}")
