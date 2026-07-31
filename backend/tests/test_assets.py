"""Tests for GARUDA Asset Library."""

import tempfile
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from database.connection import Base, engine
from main import app

Base.metadata.create_all(bind=engine)

client = TestClient(app)


def get_test_project() -> str:
    response = client.post(
        "/api/v1/projects",
        json={"name": f"Asset Test {uuid.uuid4().hex[:8]}"},
    )
    return response.json()["id"]


def create_test_file(tmp_dir: Path, name: str, content: bytes = b"test") -> Path:
    file_path = tmp_dir / name
    file_path.write_bytes(content)
    return file_path


def test_import_asset():
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = create_test_file(Path(tmp_dir), "asset_test.txt")

        with open(file_path, "rb") as f:
            response = client.post(
                f"/api/v1/assets/import?project_id={project_id}&name=Test%20Asset",
                files={"file": ("asset_test.txt", f, "text/plain")},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["asset_id"] is not None
        assert data["is_duplicate"] is False


def test_import_geojson_asset():
    project_id = get_test_project()

    import json
    with tempfile.TemporaryDirectory() as tmp_dir:
        geojson = {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [77, 28]}, "properties": {"name": "test"}}],
        }
        file_path = Path(tmp_dir) / "aoi.geojson"
        file_path.write_text(json.dumps(geojson))

        with open(file_path, "rb") as f:
            response = client.post(
                f"/api/v1/assets/import?project_id={project_id}&name=Test%20AOI&category=satellite",
                files={"file": ("aoi.geojson", f, "application/json")},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True


def test_asset_duplicate_detection():
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = create_test_file(Path(tmp_dir), "dup.txt", b"same content")

        for _ in range(2):
            with open(file_path, "rb") as f:
                client.post(
                    f"/api/v1/assets/import?project_id={project_id}",
                    files={"file": ("dup.txt", f, "text/plain")},
                )

        response = client.get(f"/api/v1/assets/stats/{project_id}")
        assert response.status_code == 200
        stats = response.json()
        assert stats["total"] == 1


def test_list_assets():
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = create_test_file(Path(tmp_dir), "list_asset.txt")

        with open(file_path, "rb") as f:
            client.post(
                f"/api/v1/assets/import?project_id={project_id}",
                files={"file": ("list_asset.txt", f, "text/plain")},
            )

        response = client.get(f"/api/v1/assets?project_id={project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert "assets" in data


def test_search_assets():
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = create_test_file(Path(tmp_dir), "searchable.txt")

        with open(file_path, "rb") as f:
            client.post(
                f"/api/v1/assets/import?project_id={project_id}&name=searchable_asset",
                files={"file": ("searchable.txt", f, "text/plain")},
            )

        response = client.get(
            f"/api/v1/assets/search?project_id={project_id}&q=searchable"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


def test_delete_asset():
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = create_test_file(Path(tmp_dir), "delete_me.txt")

        with open(file_path, "rb") as f:
            import_response = client.post(
                f"/api/v1/assets/import?project_id={project_id}",
                files={"file": ("delete_me.txt", f, "text/plain")},
            )

        asset_id = import_response.json()["asset_id"]

        response = client.delete(f"/api/v1/assets/{asset_id}")
        assert response.status_code == 200

        response = client.get(f"/api/v1/assets/{asset_id}")
        assert response.status_code == 404


def test_favorite_toggle():
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = create_test_file(Path(tmp_dir), "fav.txt")

        with open(file_path, "rb") as f:
            import_response = client.post(
                f"/api/v1/assets/import?project_id={project_id}",
                files={"file": ("fav.txt", f, "text/plain")},
            )

        asset_id = import_response.json()["asset_id"]

        response = client.post(f"/api/v1/assets/{asset_id}/favorite")
        assert response.status_code == 200
        assert response.json()["is_favorite"] is True

        response = client.post(f"/api/v1/assets/{asset_id}/favorite")
        assert response.status_code == 200
        assert response.json()["is_favorite"] is False


def test_pin_toggle():
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = create_test_file(Path(tmp_dir), "pin.txt")

        with open(file_path, "rb") as f:
            import_response = client.post(
                f"/api/v1/assets/import?project_id={project_id}",
                files={"file": ("pin.txt", f, "text/plain")},
            )

        asset_id = import_response.json()["asset_id"]

        response = client.post(f"/api/v1/assets/{asset_id}/pin")
        assert response.status_code == 200
        assert response.json()["is_pinned"] is True

        response = client.post(f"/api/v1/assets/{asset_id}/pin")
        assert response.status_code == 200
        assert response.json()["is_pinned"] is False


def test_archive_restore():
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = create_test_file(Path(tmp_dir), "archive.txt")

        with open(file_path, "rb") as f:
            import_response = client.post(
                f"/api/v1/assets/import?project_id={project_id}",
                files={"file": ("archive.txt", f, "text/plain")},
            )

        asset_id = import_response.json()["asset_id"]

        response = client.post(f"/api/v1/assets/{asset_id}/archive")
        assert response.status_code == 200
        assert response.json()["success"] is True

        response = client.post(f"/api/v1/assets/{asset_id}/restore")
        assert response.status_code == 200
        assert response.json()["success"] is True


def test_asset_history():
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = create_test_file(Path(tmp_dir), "history.txt")

        with open(file_path, "rb") as f:
            import_response = client.post(
                f"/api/v1/assets/import?project_id={project_id}",
                files={"file": ("history.txt", f, "text/plain")},
            )

        asset_id = import_response.json()["asset_id"]

        response = client.get(f"/api/v1/assets/{asset_id}/history")
        assert response.status_code == 200
        history = response.json()
        assert len(history) >= 1
        assert history[0]["action"] in ("created", "imported")


def test_asset_stats():
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = create_test_file(Path(tmp_dir), "stats.txt", b"stats content")

        with open(file_path, "rb") as f:
            client.post(
                f"/api/v1/assets/import?project_id={project_id}",
                files={"file": ("stats.txt", f, "text/plain")},
            )

        response = client.get(f"/api/v1/assets/stats/{project_id}")
        assert response.status_code == 200
        stats = response.json()
        assert stats["total"] >= 1
        assert stats["total_size_bytes"] >= 14


def test_add_tag():
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = create_test_file(Path(tmp_dir), "tagged.txt")

        with open(file_path, "rb") as f:
            import_response = client.post(
                f"/api/v1/assets/import?project_id={project_id}",
                files={"file": ("tagged.txt", f, "text/plain")},
            )

        asset_id = import_response.json()["asset_id"]

        response = client.post(f"/api/v1/assets/{asset_id}/tag", json={"tag": "important"})
        assert response.status_code == 200

        # Verify tag via history
        history = client.get(f"/api/v1/assets/{asset_id}/history").json()
        assert any(h["action"] == "created" for h in history)


def test_asset_relationships():
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path1 = create_test_file(Path(tmp_dir), "source.txt")
        file_path2 = create_test_file(Path(tmp_dir), "target.txt", b"target content")

        with open(file_path1, "rb") as f:
            r1 = client.post(
                f"/api/v1/assets/import?project_id={project_id}",
                files={"file": ("source.txt", f, "text/plain")},
            )

        with open(file_path2, "rb") as f:
            r2 = client.post(
                f"/api/v1/assets/import?project_id={project_id}",
                files={"file": ("target.txt", f, "text/plain")},
            )

        source_id = r1.json()["asset_id"]
        target_id = r2.json()["asset_id"]

        response = client.post(
            f"/api/v1/assets/{source_id}/relationship",
            json={"target_asset_id": target_id, "relationship_type": "derived_from"},
        )
        assert response.status_code == 200

        response = client.get(f"/api/v1/assets/{source_id}/related")
        assert response.status_code == 200
        related = response.json()
        assert len(related["related"]) >= 1


def test_collections():
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = create_test_file(Path(tmp_dir), "col_asset.txt")

        with open(file_path, "rb") as f:
            import_response = client.post(
                f"/api/v1/assets/import?project_id={project_id}",
                files={"file": ("col_asset.txt", f, "text/plain")},
            )

        asset_id = import_response.json()["asset_id"]

        # Create collection
        response = client.post(
            "/api/v1/assets/collections",
            json={"name": "Test Collection", "project_id": project_id},
        )
        assert response.status_code == 201
        collection_id = response.json()["id"]

        # Add asset to collection
        response = client.post(f"/api/v1/assets/collections/{collection_id}/add?asset_id={asset_id}")
        assert response.status_code == 200

        # Get collection assets
        response = client.get(f"/api/v1/assets/collections/{collection_id}/assets")
        assert response.status_code == 200
        assets = response.json()
        assert len(assets) >= 1
