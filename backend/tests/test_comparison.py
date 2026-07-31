"""Tests for GARUDA Temporal Comparison Engine."""

import json
import os
import tempfile
import uuid
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from database.connection import Base, engine
from main import app

Base.metadata.create_all(bind=engine)

client = TestClient(app)


def get_test_project() -> str:
    """Create a test project and return its ID."""
    response = client.post(
        "/api/v1/projects",
        json={"name": f"Comp Test {uuid.uuid4().hex[:8]}"},
    )
    return response.json()["id"]


def create_test_image(tmp_dir: Path, name: str = "test.png", size=(100, 100)) -> Path:
    """Create a test image."""
    file_path = tmp_dir / name
    img = np.random.randint(0, 255, (size[1], size[0]), dtype=np.uint8)
    cv2.imwrite(str(file_path), img)
    return file_path


def create_shifted_image(tmp_dir: Path, reference_path: Path, shift=(5, 3)) -> Path:
    """Create a shifted version of the reference image."""
    ref = cv2.imread(str(reference_path), cv2.IMREAD_GRAYSCALE)
    M = np.float32([[1, 0, shift[0]], [0, 1, shift[1]]])
    shifted = cv2.warpAffine(ref, M, (ref.shape[1], ref.shape[0]))
    out_path = tmp_dir / "shifted.png"
    cv2.imwrite(str(out_path), shifted)
    return out_path


# --- Session Service Tests ---


class TestSessionService:
    """Tests for session management service."""

    def test_create_session(self, db_session):
        from comparison_engine.services.session_service import SessionService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Test Session",
            dataset_paths=[str(img_a), str(img_b)],
        )
        assert session.id is not None
        assert session.name == "Test Session"
        assert session.mode == "side_by_side"

    def test_create_session_insufficient_datasets(self, db_session):
        from comparison_engine.services.session_service import SessionService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img = create_test_image(tmp, "a.png")

        with pytest.raises(ValueError, match="At least 2 datasets"):
            SessionService.create_session(
                db=db_session,
                project_id=project_id,
                name="Bad",
                dataset_paths=[str(img)],
            )

    def test_create_session_with_labels(self, db_session):
        from comparison_engine.services.session_service import SessionService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Labeled",
            dataset_paths=[str(img_a), str(img_b)],
            dataset_labels=["Before", "After"],
        )
        labels = json.loads(session.dataset_labels)
        assert labels == ["Before", "After"]

    def test_list_sessions(self, db_session):
        from comparison_engine.services.session_service import SessionService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="List Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        sessions = SessionService.list_sessions(db_session, project_id)
        assert len(sessions) >= 1

    def test_update_session(self, db_session):
        from comparison_engine.services.session_service import SessionService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Update Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        updated = SessionService.update_session(
            db_session, session.id, name="Updated Name", opacity=0.5
        )
        assert updated.name == "Updated Name"
        assert updated.opacity == 0.5

    def test_delete_session(self, db_session):
        from comparison_engine.services.session_service import SessionService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Delete Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        deleted = SessionService.delete_session(db_session, session.id)
        assert deleted is True
        assert SessionService.get_session(db_session, session.id) is None

    def test_toggle_favorite(self, db_session):
        from comparison_engine.services.session_service import SessionService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Fav Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        session = SessionService.toggle_favorite(db_session, session.id)
        assert session.favorite is True
        session = SessionService.toggle_favorite(db_session, session.id)
        assert session.favorite is False

    def test_get_views(self, db_session):
        from comparison_engine.services.session_service import SessionService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Views Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        views = SessionService.get_views(db_session, session.id)
        assert len(views) == 2
        assert views[0].view_index == 0
        assert views[1].view_index == 1


# --- Timeline Service Tests ---


class TestTimelineService:
    """Tests for timeline navigation."""

    def test_set_position(self, db_session):
        from comparison_engine.services.session_service import SessionService
        from comparison_engine.services.timeline_service import TimelineService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Timeline Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        updated = TimelineService.set_position(db_session, session.id, 5)
        assert updated.timeline_position == 5

    def test_previous_date(self, db_session):
        from comparison_engine.services.session_service import SessionService
        from comparison_engine.services.timeline_service import TimelineService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Prev Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        TimelineService.set_position(db_session, session.id, 5)
        updated = TimelineService.previous_date(db_session, session.id)
        assert updated.timeline_position == 4

    def test_next_date(self, db_session):
        from comparison_engine.services.session_service import SessionService
        from comparison_engine.services.timeline_service import TimelineService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Next Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        updated = TimelineService.next_date(db_session, session.id)
        assert updated.timeline_position == 1

    def test_playback(self, db_session):
        from comparison_engine.services.session_service import SessionService
        from comparison_engine.services.timeline_service import TimelineService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Playback Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        session = TimelineService.start_playback(db_session, session.id, 2.0)
        assert session.is_playing is True
        assert session.playback_speed == 2.0

        session = TimelineService.pause_playback(db_session, session.id)
        assert session.is_playing is False

    def test_toggle_loop(self, db_session):
        from comparison_engine.services.session_service import SessionService
        from comparison_engine.services.timeline_service import TimelineService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Loop Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        session = TimelineService.toggle_loop(db_session, session.id)
        assert session.is_looping is True
        session = TimelineService.toggle_loop(db_session, session.id)
        assert session.is_looping is False

    def test_get_timeline_state(self, db_session):
        from comparison_engine.services.session_service import SessionService
        from comparison_engine.services.timeline_service import TimelineService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="State Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        state = TimelineService.get_timeline_state(db_session, session.id)
        assert "position" in state
        assert "is_playing" in state
        assert "available_speeds" in state


# --- Sync Service Tests ---


class TestSyncService:
    """Tests for synchronization service."""

    def test_get_sync_options(self, db_session):
        from comparison_engine.services.session_service import SessionService
        from comparison_engine.services.sync_service import SyncService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Sync Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        options = SyncService.get_sync_options(db_session, session.id)
        assert "enabled" in options
        assert "available" in options

    def test_set_sync_options(self, db_session):
        from comparison_engine.services.session_service import SessionService
        from comparison_engine.services.sync_service import SyncService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Sync Set Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        session = SyncService.set_sync_options(
            db_session, session.id, ["pan", "zoom", "rotation"]
        )
        enabled = json.loads(session.sync_options)
        assert "pan" in enabled
        assert "rotation" in enabled

    def test_toggle_sync_option(self, db_session):
        from comparison_engine.services.session_service import SessionService
        from comparison_engine.services.sync_service import SyncService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Sync Toggle Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        session = SyncService.toggle_sync_option(db_session, session.id, "rotation")
        enabled = json.loads(session.sync_options)
        assert "rotation" in enabled

        session = SyncService.toggle_sync_option(db_session, session.id, "rotation")
        enabled = json.loads(session.sync_options)
        assert "rotation" not in enabled

    def test_update_map_state(self, db_session):
        from comparison_engine.services.session_service import SessionService
        from comparison_engine.services.sync_service import SyncService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Map State Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        session = SyncService.update_map_state(
            db_session, session.id,
            center=[77.5, 28.5],
            zoom=12.0,
        )
        state = SyncService.get_map_state(db_session, session.id)
        assert state["center"] == [77.5, 28.5]
        assert state["zoom"] == 12.0


# --- Difference Service Tests ---


class TestDifferenceService:
    """Tests for difference visualization."""

    def test_absolute_difference(self, tmp_path):
        from comparison_engine.services.difference_service import DifferenceService
        img_a = create_test_image(tmp_path, "a.png")
        img_b = create_shifted_image(tmp_path, img_a)

        diff, stats = DifferenceService.compute_absolute_difference(
            str(img_a), str(img_b)
        )
        assert diff is not None
        assert "mean_diff" in stats
        assert "max_diff" in stats

    def test_thresholded_difference(self, tmp_path):
        from comparison_engine.services.difference_service import DifferenceService
        img_a = create_test_image(tmp_path, "a.png")
        img_b = create_shifted_image(tmp_path, img_a)

        diff, stats = DifferenceService.compute_thresholded_difference(
            str(img_a), str(img_b), threshold=0.1
        )
        assert diff is not None
        assert "changed_pixels" in stats
        assert "change_ratio" in stats

    def test_false_color_difference(self, tmp_path):
        from comparison_engine.services.difference_service import DifferenceService
        img_a = create_test_image(tmp_path, "a.png")
        img_b = create_shifted_image(tmp_path, img_a)

        diff, stats = DifferenceService.compute_false_color_difference(
            str(img_a), str(img_b)
        )
        assert diff is not None
        assert diff.ndim == 3
        assert diff.shape[2] == 3

    def test_histogram_comparison(self, tmp_path):
        from comparison_engine.services.difference_service import DifferenceService
        img_a = create_test_image(tmp_path, "a.png")
        img_b = create_shifted_image(tmp_path, img_a)

        result = DifferenceService.compute_histogram_comparison(
            str(img_a), str(img_b)
        )
        assert "histogram_a" in result
        assert "histogram_b" in result
        assert "correlation" in result
        assert "chi_squared_distance" in result

    def test_generate_preview(self, tmp_path):
        from comparison_engine.services.difference_service import DifferenceService
        img_a = create_test_image(tmp_path, "a.png")
        img_b = create_shifted_image(tmp_path, img_a)

        result = DifferenceService.generate_difference_preview(
            str(img_a), str(img_b),
            diff_type="absolute",
            output_dir=str(tmp_path / "diff_out"),
        )
        assert result["type"] == "absolute"
        assert result["output_path"] is not None
        assert os.path.exists(result["output_path"])


# --- Bookmark Service Tests ---


class TestBookmarkService:
    """Tests for bookmark service."""

    def test_create_bookmark(self, db_session):
        from comparison_engine.services.bookmark_service import BookmarkService
        from comparison_engine.services.session_service import SessionService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Bookmark Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        bm = BookmarkService.create_bookmark(
            db=db_session,
            session_id=session.id,
            name="Test Bookmark",
            timeline_position=5,
        )
        assert bm.name == "Test Bookmark"
        assert bm.timeline_position == 5

    def test_list_bookmarks(self, db_session):
        from comparison_engine.services.bookmark_service import BookmarkService
        from comparison_engine.services.session_service import SessionService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="BM List Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        BookmarkService.create_bookmark(db=db_session, session_id=session.id, name="BM1")
        BookmarkService.create_bookmark(db=db_session, session_id=session.id, name="BM2")

        bookmarks = BookmarkService.get_bookmarks(db_session, session.id)
        assert len(bookmarks) == 2

    def test_delete_bookmark(self, db_session):
        from comparison_engine.services.bookmark_service import BookmarkService
        from comparison_engine.services.session_service import SessionService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="BM Delete Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        bm = BookmarkService.create_bookmark(
            db=db_session, session_id=session.id, name="To Delete"
        )
        deleted = BookmarkService.delete_bookmark(db_session, bm.id, session.id)
        assert deleted is True


# --- Annotation Service Tests ---


class TestAnnotationService:
    """Tests for annotation service."""

    def test_create_annotation(self, db_session):
        from comparison_engine.services.annotation_service import AnnotationService
        from comparison_engine.services.session_service import SessionService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Annot Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        ann = AnnotationService.create_annotation(
            db=db_session,
            session_id=session.id,
            annotation_type="point",
            geometry={"x": 50, "y": 50},
            label="Test Point",
        )
        assert ann.annotation_type == "point"
        assert ann.label == "Test Point"

    def test_list_annotations(self, db_session):
        from comparison_engine.services.annotation_service import AnnotationService
        from comparison_engine.services.session_service import SessionService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Annot List Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        AnnotationService.create_annotation(
            db=db_session,
            session_id=session.id,
            annotation_type="point",
            geometry={"x": 10, "y": 10},
        )
        AnnotationService.create_annotation(
            db=db_session,
            session_id=session.id,
            annotation_type="line",
            geometry={"start": [0, 0], "end": [100, 100]},
        )

        annotations = AnnotationService.get_annotations(db_session, session.id)
        assert len(annotations) == 2

    def test_delete_annotation(self, db_session):
        from comparison_engine.services.annotation_service import AnnotationService
        from comparison_engine.services.session_service import SessionService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Annot Del Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        ann = AnnotationService.create_annotation(
            db=db_session,
            session_id=session.id,
            annotation_type="point",
            geometry={"x": 10, "y": 10},
        )
        deleted = AnnotationService.delete_annotation(db_session, ann.id, session.id)
        assert deleted is True


# --- Measurement Service Tests ---


class TestMeasurementService:
    """Tests for measurement service."""

    def test_create_measurement(self, db_session):
        from comparison_engine.services.measurement_service import MeasurementService
        from comparison_engine.services.session_service import SessionService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        session = SessionService.create_session(
            db=db_session,
            project_id=project_id,
            name="Meas Test",
            dataset_paths=[str(img_a), str(img_b)],
        )

        m = MeasurementService.create_measurement(
            db=db_session,
            session_id=session.id,
            measurement_type="distance",
            value=42.5,
            geometry={"start": [0, 0], "end": [100, 100]},
        )
        assert m.value == 42.5
        assert m.measurement_type == "distance"

    def test_compute_distance(self):
        from comparison_engine.services.measurement_service import MeasurementService
        result = MeasurementService.compute_distance(0, 0, 3, 4)
        assert result["pixel_distance"] == 5.0

    def test_compute_area(self):
        from comparison_engine.services.measurement_service import MeasurementService
        # Simple square
        coords = [[0, 0], [10, 0], [10, 10], [0, 10]]
        result = MeasurementService.compute_area(coords)
        assert result["area"] == 100.0
        assert result["vertex_count"] == 4


# --- API Endpoint Tests ---


class TestComparisonAPI:
    """Tests for comparison API endpoints."""

    def test_get_config(self):
        response = client.get("/api/v1/comparisons/config")
        assert response.status_code == 200
        data = response.json()
        assert "modes" in data
        assert "side_by_side" in data["modes"]

    def test_create_session_api(self):
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        response = client.post(
            f"/api/v1/comparisons/project/{project_id}",
            json={
                "name": "API Session",
                "dataset_paths": [str(img_a), str(img_b)],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Session"
        assert len(data["dataset_paths"]) == 2

    def test_list_sessions_api(self):
        project_id = get_test_project()
        response = client.get(f"/api/v1/comparisons/project/{project_id}")
        assert response.status_code == 200

    def test_get_session_api(self):
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        create_resp = client.post(
            f"/api/v1/comparisons/project/{project_id}",
            json={
                "name": "Get Test",
                "dataset_paths": [str(img_a), str(img_b)],
            },
        )
        session_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/comparisons/{session_id}")
        assert response.status_code == 200
        assert response.json()["id"] == session_id

    def test_update_session_api(self):
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        create_resp = client.post(
            f"/api/v1/comparisons/project/{project_id}",
            json={
                "name": "Update API Test",
                "dataset_paths": [str(img_a), str(img_b)],
            },
        )
        session_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/v1/comparisons/{session_id}",
            json={"name": "Updated API", "opacity": 0.7},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated API"

    def test_delete_session_api(self):
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        create_resp = client.post(
            f"/api/v1/comparisons/project/{project_id}",
            json={
                "name": "Delete API Test",
                "dataset_paths": [str(img_a), str(img_b)],
            },
        )
        session_id = create_resp.json()["id"]

        response = client.delete(f"/api/v1/comparisons/{session_id}")
        assert response.status_code == 204

    def test_timeline_endpoints(self):
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        create_resp = client.post(
            f"/api/v1/comparisons/project/{project_id}",
            json={
                "name": "Timeline API",
                "dataset_paths": [str(img_a), str(img_b)],
            },
        )
        session_id = create_resp.json()["id"]

        # Get timeline
        resp = client.get(f"/api/v1/comparisons/{session_id}/timeline")
        assert resp.status_code == 200

        # Set position
        resp = client.patch(
            f"/api/v1/comparisons/{session_id}/timeline/position?position=5"
        )
        assert resp.status_code == 200

        # Next
        resp = client.post(f"/api/v1/comparisons/{session_id}/timeline/next")
        assert resp.status_code == 200

        # Previous
        resp = client.post(f"/api/v1/comparisons/{session_id}/timeline/previous")
        assert resp.status_code == 200

        # Play
        resp = client.post(f"/api/v1/comparisons/{session_id}/timeline/play?speed=2.0")
        assert resp.status_code == 200

        # Pause
        resp = client.post(f"/api/v1/comparisons/{session_id}/timeline/pause")
        assert resp.status_code == 200

    def test_sync_endpoints(self):
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        create_resp = client.post(
            f"/api/v1/comparisons/project/{project_id}",
            json={
                "name": "Sync API",
                "dataset_paths": [str(img_a), str(img_b)],
            },
        )
        session_id = create_resp.json()["id"]

        # Get sync options
        resp = client.get(f"/api/v1/comparisons/{session_id}/sync")
        assert resp.status_code == 200

        # Set sync options
        resp = client.patch(
            f"/api/v1/comparisons/{session_id}/sync",
            json={"enabled": ["pan", "zoom", "cursor"]},
        )
        assert resp.status_code == 200

        # Toggle sync
        resp = client.patch(
            f"/api/v1/comparisons/{session_id}/sync/toggle/rotation"
        )
        assert resp.status_code == 200

    def test_bookmark_crud_api(self):
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        create_resp = client.post(
            f"/api/v1/comparisons/project/{project_id}",
            json={
                "name": "Bookmark API",
                "dataset_paths": [str(img_a), str(img_b)],
            },
        )
        session_id = create_resp.json()["id"]

        # Create
        resp = client.post(
            f"/api/v1/comparisons/{session_id}/bookmarks",
            json={"name": "Test BM", "timeline_position": 5},
        )
        assert resp.status_code == 201
        bm_id = resp.json()["id"]

        # List
        resp = client.get(f"/api/v1/comparisons/{session_id}/bookmarks")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

        # Delete
        resp = client.delete(
            f"/api/v1/comparisons/{session_id}/bookmarks/{bm_id}"
        )
        assert resp.status_code == 204

    def test_annotation_crud_api(self):
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        create_resp = client.post(
            f"/api/v1/comparisons/project/{project_id}",
            json={
                "name": "Annot API",
                "dataset_paths": [str(img_a), str(img_b)],
            },
        )
        session_id = create_resp.json()["id"]

        # Create
        resp = client.post(
            f"/api/v1/comparisons/{session_id}/annotations",
            json={
                "annotation_type": "point",
                "geometry": {"x": 50, "y": 50},
                "label": "API Point",
            },
        )
        assert resp.status_code == 201
        ann_id = resp.json()["id"]

        # List
        resp = client.get(f"/api/v1/comparisons/{session_id}/annotations")
        assert resp.status_code == 200

        # Delete
        resp = client.delete(
            f"/api/v1/comparisons/{session_id}/annotations/{ann_id}"
        )
        assert resp.status_code == 204

    def test_measurement_crud_api(self):
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        create_resp = client.post(
            f"/api/v1/comparisons/project/{project_id}",
            json={
                "name": "Meas API",
                "dataset_paths": [str(img_a), str(img_b)],
            },
        )
        session_id = create_resp.json()["id"]

        # Create
        resp = client.post(
            f"/api/v1/comparisons/{session_id}/measurements",
            json={
                "measurement_type": "distance",
                "value": 42.5,
                "geometry": {"start": [0, 0], "end": [100, 100]},
            },
        )
        assert resp.status_code == 201

        # List
        resp = client.get(f"/api/v1/comparisons/{session_id}/measurements")
        assert resp.status_code == 200

    def test_difference_preview_api(self):
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        response = client.post(
            "/api/v1/comparisons/difference/preview",
            json={
                "file_a": str(img_a),
                "file_b": str(img_b),
                "diff_type": "absolute",
            },
        )
        assert response.status_code == 200
        assert "type" in response.json()

    def test_export_json_api(self):
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        create_resp = client.post(
            f"/api/v1/comparisons/project/{project_id}",
            json={
                "name": "Export API",
                "dataset_paths": [str(img_a), str(img_b)],
            },
        )
        session_id = create_resp.json()["id"]

        response = client.post(f"/api/v1/comparisons/{session_id}/exports/json")
        assert response.status_code == 200
        assert "session" in response.json()

    def test_views_api(self):
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        img_a = create_test_image(tmp, "a.png")
        img_b = create_shifted_image(tmp, img_a)

        create_resp = client.post(
            f"/api/v1/comparisons/project/{project_id}",
            json={
                "name": "Views API",
                "dataset_paths": [str(img_a), str(img_b)],
            },
        )
        session_id = create_resp.json()["id"]

        resp = client.get(f"/api/v1/comparisons/{session_id}/views")
        assert resp.status_code == 200
        assert len(resp.json()) == 2
