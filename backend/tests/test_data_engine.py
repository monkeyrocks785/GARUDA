"""Tests for GARUDA Data Engine."""

import json
import tempfile
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from database.connection import Base, engine
from main import app

# Create tables for testing
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def get_test_project() -> str:
    """Create a test project and return its ID."""
    response = client.post(
        "/api/v1/projects",
        json={"name": f"Data Engine Test {uuid.uuid4().hex[:8]}"},
    )
    return response.json()["id"]


def create_test_file(tmp_dir: Path, name: str, content: bytes = b"test") -> Path:
    """Create a test file."""
    file_path = tmp_dir / name
    file_path.write_bytes(content)
    return file_path


def test_import_geojson():
    """Test importing a GeoJSON file."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a simple GeoJSON
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "properties": {"name": "test"},
                }
            ],
        }
        file_path = Path(tmp_dir) / "test.geojson"
        file_path.write_text(json.dumps(geojson))

        with open(file_path, "rb") as f:
            response = client.post(
                f"/api/v1/datasets/import?project_id={project_id}",
                files={"file": ("test.geojson", f, "application/json")},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["dataset_id"] is not None
        assert data["is_duplicate"] is False


def test_import_csv():
    """Test importing a CSV file."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = Path(tmp_dir) / "data.csv"
        file_path.write_text("name,value\ntest,123")

        with open(file_path, "rb") as f:
            response = client.post(
                f"/api/v1/datasets/import?project_id={project_id}",
                files={"file": ("data.csv", f, "text/csv")},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True


def test_duplicate_detection():
    """Test duplicate detection by checksum."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = Path(tmp_dir) / "duplicate.txt"
        file_path.write_text("same content")

        # Import twice
        for _ in range(2):
            with open(file_path, "rb") as f:
                client.post(
                    f"/api/v1/datasets/import?project_id={project_id}",
                    files={"file": ("duplicate.txt", f, "text/plain")},
                )

        # Check stats
        response = client.get(f"/api/v1/datasets/stats/{project_id}")
        assert response.status_code == 200
        stats = response.json()
        assert stats["total"] == 1  # Only one dataset, not two


def test_list_datasets():
    """Test listing datasets."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Import a file
        file_path = Path(tmp_dir) / "list_test.txt"
        file_path.write_text("list test")

        with open(file_path, "rb") as f:
            client.post(
                f"/api/v1/datasets/import?project_id={project_id}",
                files={"file": ("list_test.txt", f, "text/plain")},
            )

        # List datasets
        response = client.get(f"/api/v1/datasets?project_id={project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


def test_search_datasets():
    """Test searching datasets."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = Path(tmp_dir) / "searchable.txt"
        file_path.write_text("search test")

        with open(file_path, "rb") as f:
            client.post(
                f"/api/v1/datasets/import?project_id={project_id}&name=searchable_dataset",
                files={"file": ("searchable.txt", f, "text/plain")},
            )

        # Search by name
        response = client.get(
            f"/api/v1/datasets/search?project_id={project_id}&q=searchable"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


def test_delete_dataset():
    """Test deleting a dataset."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = Path(tmp_dir) / "delete_me.txt"
        file_path.write_text("delete me")

        # Import
        with open(file_path, "rb") as f:
            import_response = client.post(
                f"/api/v1/datasets/import?project_id={project_id}",
                files={"file": ("delete_me.txt", f, "text/plain")},
            )

        dataset_id = import_response.json()["dataset_id"]

        # Delete
        response = client.delete(f"/api/v1/datasets/{dataset_id}")
        assert response.status_code == 200

        # Verify deleted
        response = client.get(f"/api/v1/datasets/{dataset_id}")
        assert response.status_code == 404


def test_favorite_toggle():
    """Test toggling favorite status."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = Path(tmp_dir) / "fav_test.txt"
        file_path.write_text("favorite")

        with open(file_path, "rb") as f:
            import_response = client.post(
                f"/api/v1/datasets/import?project_id={project_id}",
                files={"file": ("fav_test.txt", f, "text/plain")},
            )

        dataset_id = import_response.json()["dataset_id"]

        # Toggle favorite
        response = client.post(f"/api/v1/datasets/{dataset_id}/favorite")
        assert response.status_code == 200
        assert response.json()["is_favorite"] is True

        # Toggle back
        response = client.post(f"/api/v1/datasets/{dataset_id}/favorite")
        assert response.status_code == 200
        assert response.json()["is_favorite"] is False
