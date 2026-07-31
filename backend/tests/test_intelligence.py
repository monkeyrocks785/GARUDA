"""Tests for the Intelligence Analysis Engine."""

import json
import os
import uuid

import numpy as np
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# Create a test image file for inference tests
_TEST_IMAGE_DIR = os.path.join(os.path.dirname(__file__), "_test_images")


def _ensure_test_image():
    os.makedirs(_TEST_IMAGE_DIR, exist_ok=True)
    img_path = os.path.join(_TEST_IMAGE_DIR, "test_image.tif")
    if not os.path.exists(img_path):
        try:
            import rasterio
            from rasterio.transform import from_bounds
            arr = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
            transform = from_bounds(0, 0, 1, 1, 256, 256)
            with rasterio.open(
                img_path, "w", driver="GTiff",
                height=256, width=256, count=3, dtype="uint8",
                crs="EPSG:4326", transform=transform,
            ) as dst:
                for i in range(3):
                    dst.write(arr[:, :, i], i + 1)
        except ImportError:
            from PIL import Image
            arr = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
            Image.fromarray(arr).save(img_path.replace(".tif", ".png"))
            return img_path.replace(".tif", ".png")
    return img_path


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_test_project():
    r = client.post(
        "/api/v1/projects",
        json={"name": f"Intel Test {uuid.uuid4().hex[:8]}"},
    )
    assert r.status_code == 201
    return r.json()["id"]


# ── Model Registry Tests ─────────────────────────────────────────────────────

class TestModelRegistry:
    def test_register_model(self):
        r = client.post(
            "/api/v1/intelligence/models",
            json={
                "name": "TestDetector",
                "task": "detection",
                "framework": "pytorch",
                "version": "1.0.0",
                "description": "A test detector",
                "author": "Test",
            },
        )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "TestDetector"
        assert data["task"] == "detection"
        assert data["status"] == "registered"
        assert data["is_loaded"] is False

    def test_register_model_invalid_task(self):
        r = client.post(
            "/api/v1/intelligence/models",
            json={"name": "Bad", "task": "invalid_task"},
        )
        assert r.status_code == 400

    def test_list_models(self):
        r = client.get("/api/v1/intelligence/models")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_model(self):
        r = client.post(
            "/api/v1/intelligence/models",
            json={"name": "GetTest", "task": "detection"},
        )
        model_id = r.json()["id"]
        r = client.get(f"/api/v1/intelligence/models/{model_id}")
        assert r.status_code == 200
        assert r.json()["name"] == "GetTest"

    def test_get_nonexistent_model(self):
        r = client.get("/api/v1/intelligence/models/nonexistent")
        assert r.status_code == 404

    def test_load_model(self):
        r = client.post(
            "/api/v1/intelligence/models",
            json={"name": "LoadTest", "task": "detection"},
        )
        model_id = r.json()["id"]
        r = client.post(f"/api/v1/intelligence/models/{model_id}/load")
        assert r.status_code == 200
        assert r.json()["is_loaded"] is True
        assert r.json()["status"] == "ready"

    def test_unload_model(self):
        r = client.post(
            "/api/v1/intelligence/models",
            json={"name": "UnloadTest", "task": "detection"},
        )
        model_id = r.json()["id"]
        client.post(f"/api/v1/intelligence/models/{model_id}/load")
        r = client.post(f"/api/v1/intelligence/models/{model_id}/unload")
        assert r.status_code == 200
        assert r.json()["is_loaded"] is False

    def test_delete_model(self):
        r = client.post(
            "/api/v1/intelligence/models",
            json={"name": "DeleteTest", "task": "detection"},
        )
        model_id = r.json()["id"]
        r = client.delete(f"/api/v1/intelligence/models/{model_id}")
        assert r.status_code == 204
        r = client.get(f"/api/v1/intelligence/models/{model_id}")
        assert r.status_code == 404

    def test_toggle_favorite(self):
        r = client.post(
            "/api/v1/intelligence/models",
            json={"name": "FavTest", "task": "detection"},
        )
        model_id = r.json()["id"]
        r = client.patch(f"/api/v1/intelligence/models/{model_id}/favorite")
        assert r.status_code == 200
        assert r.json()["favorite"] is True
        r = client.patch(f"/api/v1/intelligence/models/{model_id}/favorite")
        assert r.json()["favorite"] is False

    def test_list_models_by_task(self):
        client.post(
            "/api/v1/intelligence/models",
            json={"name": "DetFilter", "task": "detection"},
        )
        client.post(
            "/api/v1/intelligence/models",
            json={"name": "SegFilter", "task": "segmentation"},
        )
        r = client.get("/api/v1/intelligence/models", params={"task": "detection"})
        assert r.status_code == 200
        for m in r.json():
            assert m["task"] == "detection"


# ── Analysis Job Tests ────────────────────────────────────────────────────────

class TestAnalysisJobs:
    def _create_model(self):
        r = client.post(
            "/api/v1/intelligence/models",
            json={"name": f"JobModel {uuid.uuid4().hex[:6]}", "task": "detection"},
        )
        return r.json()["id"]

    def test_create_job(self):
        pid = get_test_project()
        mid = self._create_model()
        img_path = _ensure_test_image()
        r = client.post(
            f"/api/v1/intelligence/project/{pid}/jobs",
            json={
                "name": "Test Job",
                "model_id": mid,
                "input_path": img_path,
                "task_type": "detection",
            },
        )
        assert r.status_code == 201
        assert r.json()["name"] == "Test Job"
        assert r.json()["status"] == "pending"

    def test_create_job_invalid_model(self):
        pid = get_test_project()
        img_path = _ensure_test_image()
        r = client.post(
            f"/api/v1/intelligence/project/{pid}/jobs",
            json={
                "name": "Bad Model Job",
                "model_id": "nonexistent",
                "input_path": img_path,
            },
        )
        assert r.status_code == 400

    def test_list_jobs(self):
        pid = get_test_project()
        r = client.get(f"/api/v1/intelligence/project/{pid}/jobs")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_job(self):
        pid = get_test_project()
        mid = self._create_model()
        img_path = _ensure_test_image()
        r = client.post(
            f"/api/v1/intelligence/project/{pid}/jobs",
            json={"name": "GetJob", "model_id": mid, "input_path": img_path},
        )
        job_id = r.json()["id"]
        r = client.get(f"/api/v1/intelligence/jobs/{job_id}")
        assert r.status_code == 200
        assert r.json()["name"] == "GetJob"

    def test_delete_job(self):
        pid = get_test_project()
        mid = self._create_model()
        img_path = _ensure_test_image()
        r = client.post(
            f"/api/v1/intelligence/project/{pid}/jobs",
            json={"name": "DelJob", "model_id": mid, "input_path": img_path},
        )
        job_id = r.json()["id"]
        r = client.delete(f"/api/v1/intelligence/jobs/{job_id}")
        assert r.status_code == 204

    def test_get_job_history(self):
        pid = get_test_project()
        mid = self._create_model()
        img_path = _ensure_test_image()
        r = client.post(
            f"/api/v1/intelligence/project/{pid}/jobs",
            json={"name": "HistJob", "model_id": mid, "input_path": img_path},
        )
        job_id = r.json()["id"]
        r = client.get(f"/api/v1/intelligence/jobs/{job_id}/history")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 1  # At least job_created


# ── Inference & Detection Tests ──────────────────────────────────────────────

class TestInference:
    def _create_model_and_job(self, pid):
        img_path = _ensure_test_image()
        # Create and load model
        r = client.post(
            "/api/v1/intelligence/models",
            json={"name": f"InfraDet {uuid.uuid4().hex[:6]}", "task": "detection"},
        )
        mid = r.json()["id"]
        client.post(f"/api/v1/intelligence/models/{mid}/load")

        # Create job
        r = client.post(
            f"/api/v1/intelligence/project/{pid}/jobs",
            json={
                "name": "Infra Job",
                "model_id": mid,
                "input_path": img_path,
                "task_type": "detection",
                "confidence_threshold": 0.3,
            },
        )
        return mid, r.json()["id"]

    def test_run_inference(self):
        pid = get_test_project()
        mid, job_id = self._create_model_and_job(pid)
        r = client.post(f"/api/v1/intelligence/jobs/{job_id}/run")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "completed"
        assert data["detection_count"] >= 0

    def test_list_detections(self):
        pid = get_test_project()
        mid, job_id = self._create_model_and_job(pid)
        client.post(f"/api/v1/intelligence/jobs/{job_id}/run")
        r = client.get(f"/api/v1/intelligence/jobs/{job_id}/detections")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_detections_geojson(self):
        pid = get_test_project()
        mid, job_id = self._create_model_and_job(pid)
        client.post(f"/api/v1/intelligence/jobs/{job_id}/run")
        r = client.get(f"/api/v1/intelligence/jobs/{job_id}/detections/geojson")
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "FeatureCollection"

    def test_list_project_detections(self):
        pid = get_test_project()
        mid, job_id = self._create_model_and_job(pid)
        client.post(f"/api/v1/intelligence/jobs/{job_id}/run")
        r = client.get(f"/api/v1/intelligence/project/{pid}/detections")
        assert r.status_code == 200

    def test_cancel_job(self):
        pid = get_test_project()
        mid, job_id = self._create_model_and_job(pid)
        r = client.post(f"/api/v1/intelligence/jobs/{job_id}/cancel")
        assert r.status_code == 200

    def test_review_stats(self):
        pid = get_test_project()
        mid, job_id = self._create_model_and_job(pid)
        client.post(f"/api/v1/intelligence/jobs/{job_id}/run")
        r = client.get(f"/api/v1/intelligence/jobs/{job_id}/review-stats")
        assert r.status_code == 200
        stats = r.json()
        assert "total" in stats
        assert "pending" in stats


# ── Review Workflow Tests ─────────────────────────────────────────────────────

class TestReviewWorkflow:
    def _get_detection(self):
        img_path = _ensure_test_image()
        pid = get_test_project()
        r = client.post(
            "/api/v1/intelligence/models",
            json={"name": f"RevModel {uuid.uuid4().hex[:6]}", "task": "detection"},
        )
        mid = r.json()["id"]
        client.post(f"/api/v1/intelligence/models/{mid}/load")
        r = client.post(
            f"/api/v1/intelligence/project/{pid}/jobs",
            json={
                "name": "RevJob",
                "model_id": mid,
                "input_path": img_path,
                "confidence_threshold": 0.3,
            },
        )
        job_id = r.json()["id"]
        client.post(f"/api/v1/intelligence/jobs/{job_id}/run")
        r = client.get(f"/api/v1/intelligence/jobs/{job_id}/detections")
        detections = r.json()
        return pid, job_id, detections

    def test_review_accept(self):
        pid, job_id, dets = self._get_detection()
        if not dets:
            pytest.skip("No detections generated")
        det_id = dets[0]["id"]
        r = client.patch(
            f"/api/v1/intelligence/detections/{det_id}/review",
            json={"review_status": "accepted", "reviewed_by": "analyst1"},
        )
        assert r.status_code == 200
        assert r.json()["review_status"] == "accepted"
        assert r.json()["reviewed_by"] == "analyst1"

    def test_review_reject(self):
        pid, job_id, dets = self._get_detection()
        if not dets:
            pytest.skip("No detections generated")
        det_id = dets[0]["id"]
        r = client.patch(
            f"/api/v1/intelligence/detections/{det_id}/review",
            json={"review_status": "rejected"},
        )
        assert r.status_code == 200
        assert r.json()["review_status"] == "rejected"

    def test_review_invalid_status(self):
        pid, job_id, dets = self._get_detection()
        if not dets:
            pytest.skip("No detections generated")
        det_id = dets[0]["id"]
        r = client.patch(
            f"/api/v1/intelligence/detections/{det_id}/review",
            json={"review_status": "invalid"},
        )
        assert r.status_code == 400

    def test_add_notes(self):
        pid, job_id, dets = self._get_detection()
        if not dets:
            pytest.skip("No detections generated")
        det_id = dets[0]["id"]
        r = client.patch(
            f"/api/v1/intelligence/detections/{det_id}/notes",
            json={"notes": "This looks like a building"},
        )
        assert r.status_code == 200
        assert r.json()["reviewer_notes"] == "This looks like a building"

    def test_edit_geometry(self):
        pid, job_id, dets = self._get_detection()
        if not dets:
            pytest.skip("No detections generated")
        det_id = dets[0]["id"]
        new_geo = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
        }
        r = client.patch(
            f"/api/v1/intelligence/detections/{det_id}/geometry",
            json={"geometry": new_geo},
        )
        assert r.status_code == 200
        edited = json.loads(r.json()["edited_geometry_json"])
        assert edited["type"] == "Polygon"

    def test_batch_review(self):
        pid, job_id, dets = self._get_detection()
        if len(dets) < 2:
            pytest.skip("Need at least 2 detections")
        det_ids = [d["id"] for d in dets[:2]]
        r = client.post(
            "/api/v1/intelligence/detections/batch-review",
            json={"detection_ids": det_ids, "review_status": "accepted"},
        )
        assert r.status_code == 200
        for d in r.json():
            assert d["review_status"] == "accepted"

    def test_project_review_stats(self):
        pid, job_id, dets = self._get_detection()
        r = client.get(f"/api/v1/intelligence/project/{pid}/review-stats")
        assert r.status_code == 200
        stats = r.json()
        assert "total" in stats


# ── Config Endpoint Tests ─────────────────────────────────────────────────────

class TestConfig:
    def test_get_config(self):
        r = client.get("/api/v1/intelligence/models/config")
        assert r.status_code == 200
        data = r.json()
        assert "task_types" in data
        assert "detection" in data["task_types"]
        assert "device_types" in data
        assert "review_status" in data
