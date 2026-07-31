"""Tests for GARUDA Image Registration Engine."""

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
        json={"name": f"Reg Test {uuid.uuid4().hex[:8]}"},
    )
    return response.json()["id"]


def create_test_image(tmp_dir: Path, name: str = "test.png", size=(100, 100)) -> Path:
    """Create a test image with detectable features."""
    file_path = tmp_dir / name
    img = np.random.randint(0, 255, (size[1], size[0]), dtype=np.uint8)

    # Add some structured features (circles) for better detection
    for _ in range(20):
        x = np.random.randint(10, size[0] - 10)
        y = np.random.randint(10, size[1] - 10)
        r = np.random.randint(3, 8)
        color = int(np.random.randint(100, 255))
        cv2.circle(img, (x, y), r, color, -1)

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


# --- Feature Detection Tests ---


class TestFeatureDetection:
    """Tests for feature detection service."""

    def test_create_orb_detector(self):
        from registration_engine.services.feature_detection import FeatureDetectionService
        detector = FeatureDetectionService.create_detector("orb")
        assert detector is not None

    def test_create_akaze_detector(self):
        from registration_engine.services.feature_detection import FeatureDetectionService
        detector = FeatureDetectionService.create_detector("akaze")
        assert detector is not None

    def test_create_brisk_detector(self):
        from registration_engine.services.feature_detection import FeatureDetectionService
        detector = FeatureDetectionService.create_detector("brisk")
        assert detector is not None

    def test_create_sift_detector(self):
        from registration_engine.services.feature_detection import FeatureDetectionService
        detector = FeatureDetectionService.create_detector("sift")
        assert detector is not None

    def test_create_invalid_detector(self):
        from registration_engine.services.feature_detection import FeatureDetectionService
        with pytest.raises(ValueError, match="Unsupported detector"):
            FeatureDetectionService.create_detector("invalid")

    def test_load_grayscale(self, tmp_path):
        from registration_engine.services.feature_detection import FeatureDetectionService
        img_path = create_test_image(tmp_path)
        img = FeatureDetectionService.load_image_as_grayscale(str(img_path))
        assert img.ndim == 2
        assert img.shape == (100, 100)

    def test_load_missing_file(self):
        from registration_engine.services.feature_detection import FeatureDetectionService
        with pytest.raises(FileNotFoundError):
            FeatureDetectionService.load_image_as_grayscale("/nonexistent/file.png")

    def test_detect_features(self, tmp_path):
        from registration_engine.services.feature_detection import FeatureDetectionService
        img_path = create_test_image(tmp_path)
        img = FeatureDetectionService.load_image_as_grayscale(str(img_path))
        kp, desc = FeatureDetectionService.detect_features(img, "orb")
        assert len(kp) > 0
        assert desc is not None
        assert len(desc) > 0

    def test_detect_features_from_file(self, tmp_path):
        from registration_engine.services.feature_detection import FeatureDetectionService
        img_path = create_test_image(tmp_path)
        img, kp, desc = FeatureDetectionService.detect_features_from_file(
            str(img_path), "orb"
        )
        assert img.ndim == 2
        assert len(kp) > 0

    def test_get_keypoint_count(self):
        from registration_engine.services.feature_detection import FeatureDetectionService
        assert FeatureDetectionService.get_keypoint_count(np.array([])) == 0
        assert FeatureDetectionService.get_keypoint_count(None) == 0


# --- Feature Matching Tests ---


class TestFeatureMatching:
    """Tests for feature matching service."""

    def test_match_descriptors(self, tmp_path):
        from registration_engine.services.feature_detection import FeatureDetectionService
        from registration_engine.services.feature_matching import FeatureMatchingService
        img_path = create_test_image(tmp_path)
        img, kp, desc = FeatureDetectionService.detect_features_from_file(
            str(img_path), "orb"
        )
        matches = FeatureMatchingService.match_descriptors(desc, desc, "bf", "orb")
        assert len(matches) > 0

    def test_match_empty_descriptors(self):
        from registration_engine.services.feature_matching import FeatureMatchingService
        matches = FeatureMatchingService.match_descriptors(
            np.array([]), np.array([]), "bf", "orb"
        )
        assert len(matches) == 0

    def test_match_to_points(self, tmp_path):
        from registration_engine.services.feature_detection import FeatureDetectionService
        from registration_engine.services.feature_matching import FeatureMatchingService
        img_path = create_test_image(tmp_path)
        img, kp, desc = FeatureDetectionService.detect_features_from_file(
            str(img_path), "orb"
        )
        matches = FeatureMatchingService.match_descriptors(desc, desc, "bf", "orb")
        pts_ref, pts_tgt = FeatureMatchingService.match_to_points(kp, kp, matches)
        assert pts_ref.shape[1] == 2
        assert pts_tgt.shape[1] == 2
        assert len(pts_ref) == len(matches)

    def test_compute_match_statistics(self):
        from registration_engine.services.feature_matching import FeatureMatchingService
        stats = FeatureMatchingService.compute_match_statistics([])
        assert stats["count"] == 0


# --- Transform Estimation Tests ---


class TestTransformEstimation:
    """Tests for transform estimation service."""

    def test_estimate_affine_transform(self):
        from registration_engine.services.transform_estimation import TransformEstimationService
        ref_pts = np.float32([[10, 10], [50, 10], [50, 50], [10, 50], [30, 30]])
        tgt_pts = np.float32([[15, 13], [55, 13], [55, 53], [15, 53], [35, 33]])
        matrix, mask, ratio = TransformEstimationService.estimate_transform(
            ref_pts, tgt_pts, "affine"
        )
        assert matrix is not None
        assert matrix.shape == (2, 3)
        assert ratio > 0.5

    def test_estimate_insufficient_points(self):
        from registration_engine.services.transform_estimation import TransformEstimationService
        ref_pts = np.float32([[10, 10], [50, 50]])
        tgt_pts = np.float32([[15, 13], [55, 53]])
        with pytest.raises(ValueError, match="Insufficient points"):
            TransformEstimationService.estimate_transform(
                ref_pts, tgt_pts, "affine"
            )

    def test_compute_rmse(self):
        from registration_engine.services.transform_estimation import TransformEstimationService
        ref_pts = np.float32([[10, 10], [50, 10], [50, 50], [10, 50]])
        tgt_pts = np.float32([[10, 10], [50, 10], [50, 50], [10, 50]])
        matrix = np.eye(2, 3, dtype=np.float32)
        rmse = TransformEstimationService.compute_rmse(ref_pts, tgt_pts, matrix)
        assert rmse < 0.01

    def test_compute_residuals(self):
        from registration_engine.services.transform_estimation import TransformEstimationService
        ref_pts = np.float32([[10, 10], [50, 10], [50, 50]])
        tgt_pts = np.float32([[10, 10], [50, 10], [50, 50]])
        matrix = np.eye(2, 3, dtype=np.float32)
        residuals = TransformEstimationService.compute_residuals(ref_pts, tgt_pts, matrix)
        assert len(residuals) == 3
        assert all(r < 0.01 for r in residuals)

    def test_transform_points(self):
        from registration_engine.services.transform_estimation import TransformEstimationService
        pts = np.float32([[0, 0], [10, 0], [0, 10]])
        matrix = np.float32([[1, 0, 5], [0, 1, 5]])
        transformed = TransformEstimationService.transform_points(pts, matrix)
        assert np.allclose(transformed, [[5, 5], [15, 5], [5, 15]])

    def test_matrix_serialization(self):
        from registration_engine.services.transform_estimation import TransformEstimationService
        matrix = np.float32([[1, 0, 5], [0, 1, 5]])
        data = TransformEstimationService.matrix_to_list(matrix)
        restored = TransformEstimationService.list_to_matrix(data)
        assert np.allclose(matrix, restored)

    def test_list_to_matrix_empty(self):
        from registration_engine.services.transform_estimation import TransformEstimationService
        matrix = TransformEstimationService.list_to_matrix([])
        assert np.allclose(matrix, np.eye(3))


# --- Image Warping Tests ---


class TestImageWarping:
    """Tests for image warping service."""

    def test_warp_identity(self, tmp_path):
        from registration_engine.services.image_warping import ImageWarpingService
        img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        matrix = np.eye(2, 3, dtype=np.float32)
        warped = ImageWarpingService.warp_image(img, matrix)
        assert warped.shape == img.shape

    def test_warp_translation(self, tmp_path):
        from registration_engine.services.image_warping import ImageWarpingService
        img = np.zeros((100, 100), dtype=np.uint8)
        img[10:20, 10:20] = 255
        matrix = np.float32([[1, 0, 10], [0, 1, 10]])
        warped = ImageWarpingService.warp_image(img, matrix)
        assert warped[20:30, 20:30].mean() > 200

    def test_get_interpolation_flag(self):
        from registration_engine.services.image_warping import ImageWarpingService
        assert ImageWarpingService.get_interpolation_flag("nearest") == cv2.INTER_NEAREST
        assert ImageWarpingService.get_interpolation_flag("bilinear") == cv2.INTER_LINEAR
        assert ImageWarpingService.get_interpolation_flag("cubic") == cv2.INTER_CUBIC

    def test_invalid_interpolation(self):
        from registration_engine.services.image_warping import ImageWarpingService
        with pytest.raises(ValueError, match="Unsupported resampling"):
            ImageWarpingService.get_interpolation_flag("invalid")

    def test_compute_output_bounds(self):
        from registration_engine.services.image_warping import ImageWarpingService
        matrix = np.float32([[1, 0, 5], [0, 1, 5]])
        x_min, y_min, x_max, y_max = ImageWarpingService.compute_output_bounds(
            100, 100, matrix
        )
        assert x_min == 5
        assert y_min == 5
        assert x_max == 105
        assert y_max == 105


# --- Quality Metrics Tests ---


class TestQualityMetrics:
    """Tests for quality metrics service."""

    def test_compute_overall_score(self):
        from registration_engine.services.quality_metrics import QualityMetricsService
        score = QualityMetricsService.compute_overall_score(
            rmse=1.0, inlier_ratio=0.9, matched_points=100
        )
        assert 80 <= score <= 100

    def test_compute_overall_score_poor(self):
        from registration_engine.services.quality_metrics import QualityMetricsService
        score = QualityMetricsService.compute_overall_score(
            rmse=50.0, inlier_ratio=0.2, matched_points=2
        )
        assert score < 30

    def test_quality_grade(self):
        from registration_engine.services.quality_metrics import QualityMetricsService
        assert QualityMetricsService.compute_quality_grade(95) == "A+"
        assert QualityMetricsService.compute_quality_grade(90) == "A"
        assert QualityMetricsService.compute_quality_grade(80) == "B+"
        assert QualityMetricsService.compute_quality_grade(70) == "B-"
        assert QualityMetricsService.compute_quality_grade(50) == "D"
        assert QualityMetricsService.compute_quality_grade(30) == "F"

    def test_evaluate_registration_quality(self):
        from registration_engine.services.quality_metrics import QualityMetricsService
        matrix = np.eye(2, 3, dtype=np.float64)
        residuals = np.array([0.5, 0.8, 1.0, 0.3, 0.6])
        quality = QualityMetricsService.evaluate_registration_quality(
            rmse=0.7,
            inlier_ratio=0.9,
            matched_points=50,
            inlier_count=45,
            transform_matrix=matrix,
            residuals=residuals,
        )
        assert quality["is_acceptable"] is True
        assert quality["overall_score"] > 80

    def test_get_recommended_action(self):
        from registration_engine.services.quality_metrics import QualityMetricsService
        good_quality = {
            "is_acceptable": True,
            "overall_score": 90,
            "rmse": 1.0,
            "inlier_ratio": 0.9,
            "matched_points": 100,
        }
        action = QualityMetricsService.get_recommended_action(good_quality)
        assert "excellent" in action.lower()

        bad_quality = {
            "is_acceptable": False,
            "overall_score": 20,
            "rmse": 50.0,
            "inlier_ratio": 0.1,
            "matched_points": 2,
        }
        action = QualityMetricsService.get_recommended_action(bad_quality)
        assert "poor" in action.lower()


# --- Control Point Tests ---


class TestControlPoints:
    """Tests for control point service."""

    def test_add_control_point(self, db_session):
        from registration_engine.services.control_points import ControlPointService
        from registration_engine.services.registration_service import RegistrationService

        project_id = get_test_project()
        ref_path = create_test_image(db_session.info.get("tmp_path", Path(tempfile.mkdtemp())), "ref.png")
        tgt_path = create_shifted_image(
            db_session.info.get("tmp_path", Path(tempfile.mkdtemp())), ref_path
        )

        reg = RegistrationService.create_registration(
            db=db_session,
            project_id=project_id,
            name="Test Reg",
            reference_path=str(ref_path),
            target_path=str(tgt_path),
        )

        cp = ControlPointService.add_control_point(
            db=db_session,
            registration_id=reg.id,
            ref_x=10.0,
            ref_y=20.0,
            target_x=15.0,
            target_y=23.0,
        )
        assert cp.ref_x == 10.0
        assert cp.target_x == 15.0

    def test_list_control_points(self, db_session):
        from registration_engine.services.control_points import ControlPointService
        from registration_engine.services.registration_service import RegistrationService

        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        ref_path = create_test_image(tmp, "ref.png")
        tgt_path = create_shifted_image(tmp, ref_path)

        reg = RegistrationService.create_registration(
            db=db_session,
            project_id=project_id,
            name="Test Reg",
            reference_path=str(ref_path),
            target_path=str(tgt_path),
        )

        ControlPointService.add_control_point(
            db=db_session,
            registration_id=reg.id,
            ref_x=10.0, ref_y=20.0, target_x=15.0, target_y=23.0,
        )
        ControlPointService.add_control_point(
            db=db_session,
            registration_id=reg.id,
            ref_x=50.0, ref_y=60.0, target_x=55.0, target_y=63.0,
        )

        points = ControlPointService.get_control_points(db_session, reg.id)
        assert len(points) == 2

    def test_move_control_point(self, db_session):
        from registration_engine.services.control_points import ControlPointService
        from registration_engine.services.registration_service import RegistrationService

        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        ref_path = create_test_image(tmp, "ref.png")
        tgt_path = create_shifted_image(tmp, ref_path)

        reg = RegistrationService.create_registration(
            db=db_session,
            project_id=project_id,
            name="Test Reg",
            reference_path=str(ref_path),
            target_path=str(tgt_path),
        )

        cp = ControlPointService.add_control_point(
            db=db_session,
            registration_id=reg.id,
            ref_x=10.0, ref_y=20.0, target_x=15.0, target_y=23.0,
        )

        moved = ControlPointService.move_control_point(
            db=db_session,
            point_id=cp.id,
            registration_id=reg.id,
            ref_x=30.0, ref_y=40.0, target_x=35.0, target_y=43.0,
        )
        assert moved.ref_x == 30.0
        assert moved.target_x == 35.0

    def test_delete_control_point(self, db_session):
        from registration_engine.services.control_points import ControlPointService
        from registration_engine.services.registration_service import RegistrationService

        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        ref_path = create_test_image(tmp, "ref.png")
        tgt_path = create_shifted_image(tmp, ref_path)

        reg = RegistrationService.create_registration(
            db=db_session,
            project_id=project_id,
            name="Test Reg",
            reference_path=str(ref_path),
            target_path=str(tgt_path),
        )

        cp = ControlPointService.add_control_point(
            db=db_session,
            registration_id=reg.id,
            ref_x=10.0, ref_y=20.0, target_x=15.0, target_y=23.0,
        )

        deleted = ControlPointService.delete_control_point(
            db_session, cp.id, reg.id
        )
        assert deleted is True

        remaining = ControlPointService.get_control_points(db_session, reg.id)
        assert len(remaining) == 0


# --- Registration Service Tests ---


class TestRegistrationService:
    """Tests for the main registration service."""

    def test_create_registration(self, db_session):
        from registration_engine.services.registration_service import RegistrationService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        ref_path = create_test_image(tmp, "ref.png")
        tgt_path = create_shifted_image(tmp, ref_path)

        reg = RegistrationService.create_registration(
            db=db_session,
            project_id=project_id,
            name="Test Registration",
            reference_path=str(ref_path),
            target_path=str(tgt_path),
        )
        assert reg.id is not None
        assert reg.status == "pending"
        assert reg.name == "Test Registration"

    def test_create_registration_missing_file(self, db_session):
        from registration_engine.services.registration_service import RegistrationService
        project_id = get_test_project()
        with pytest.raises(FileNotFoundError):
            RegistrationService.create_registration(
                db=db_session,
                project_id=project_id,
                name="Bad Reg",
                reference_path="/nonexistent/ref.png",
                target_path="/nonexistent/tgt.png",
            )

    def test_list_registrations(self, db_session):
        from registration_engine.services.registration_service import RegistrationService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        ref_path = create_test_image(tmp, "ref.png")
        tgt_path = create_shifted_image(tmp, ref_path)

        RegistrationService.create_registration(
            db=db_session,
            project_id=project_id,
            name="Reg 1",
            reference_path=str(ref_path),
            target_path=str(tgt_path),
        )

        regs = RegistrationService.list_registrations(db_session, project_id)
        assert len(regs) >= 1

    def test_delete_registration(self, db_session):
        from registration_engine.services.registration_service import RegistrationService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        ref_path = create_test_image(tmp, "ref.png")
        tgt_path = create_shifted_image(tmp, ref_path)

        reg = RegistrationService.create_registration(
            db=db_session,
            project_id=project_id,
            name="To Delete",
            reference_path=str(ref_path),
            target_path=str(tgt_path),
        )

        deleted = RegistrationService.delete_registration(db_session, reg.id)
        assert deleted is True
        assert RegistrationService.get_registration(db_session, reg.id) is None

    def test_toggle_favorite(self, db_session):
        from registration_engine.services.registration_service import RegistrationService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        ref_path = create_test_image(tmp, "ref.png")
        tgt_path = create_shifted_image(tmp, ref_path)

        reg = RegistrationService.create_registration(
            db=db_session,
            project_id=project_id,
            name="Fav Test",
            reference_path=str(ref_path),
            target_path=str(tgt_path),
        )

        reg = RegistrationService.toggle_favorite(db_session, reg.id)
        assert reg.favorite is True
        reg = RegistrationService.toggle_favorite(db_session, reg.id)
        assert reg.favorite is False

    def test_to_dict(self, db_session):
        from registration_engine.services.registration_service import RegistrationService
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        ref_path = create_test_image(tmp, "ref.png")
        tgt_path = create_shifted_image(tmp, ref_path)

        reg = RegistrationService.create_registration(
            db=db_session,
            project_id=project_id,
            name="Dict Test",
            reference_path=str(ref_path),
            target_path=str(tgt_path),
        )

        d = RegistrationService.to_dict(reg)
        assert "id" in d
        assert "name" in d
        assert d["name"] == "Dict Test"


# --- API Endpoint Tests ---


class TestRegistrationAPI:
    """Tests for registration API endpoints."""

    def test_get_config(self):
        response = client.get("/api/v1/registrations/config")
        assert response.status_code == 200
        data = response.json()
        assert "feature_detectors" in data
        assert "orb" in data["feature_detectors"]

    def test_create_registration_api(self):
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        ref_path = create_test_image(tmp, "ref.png")
        tgt_path = create_shifted_image(tmp, ref_path)

        response = client.post(
            f"/api/v1/registrations/project/{project_id}",
            json={
                "name": "API Test Reg",
                "reference_path": str(ref_path),
                "target_path": str(tgt_path),
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Test Reg"
        assert data["status"] == "pending"

    def test_list_registrations_api(self):
        project_id = get_test_project()
        response = client.get(f"/api/v1/registrations/project/{project_id}")
        assert response.status_code == 200

    def test_get_registration_api(self):
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        ref_path = create_test_image(tmp, "ref.png")
        tgt_path = create_shifted_image(tmp, ref_path)

        create_resp = client.post(
            f"/api/v1/registrations/project/{project_id}",
            json={
                "name": "Get Test",
                "reference_path": str(ref_path),
                "target_path": str(tgt_path),
            },
        )
        reg_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/registrations/{reg_id}")
        assert response.status_code == 200
        assert response.json()["id"] == reg_id

    def test_get_nonexistent_registration(self):
        response = client.get(f"/api/v1/registrations/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_delete_registration_api(self):
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        ref_path = create_test_image(tmp, "ref.png")
        tgt_path = create_shifted_image(tmp, ref_path)

        create_resp = client.post(
            f"/api/v1/registrations/project/{project_id}",
            json={
                "name": "Delete Test",
                "reference_path": str(ref_path),
                "target_path": str(tgt_path),
            },
        )
        reg_id = create_resp.json()["id"]

        response = client.delete(f"/api/v1/registrations/{reg_id}")
        assert response.status_code == 204

    def test_toggle_favorite_api(self):
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        ref_path = create_test_image(tmp, "ref.png")
        tgt_path = create_shifted_image(tmp, ref_path)

        create_resp = client.post(
            f"/api/v1/registrations/project/{project_id}",
            json={
                "name": "Fav API Test",
                "reference_path": str(ref_path),
                "target_path": str(tgt_path),
            },
        )
        reg_id = create_resp.json()["id"]

        response = client.patch(f"/api/v1/registrations/{reg_id}/favorite")
        assert response.status_code == 200
        assert response.json()["favorite"] is True

    def test_control_points_crud_api(self):
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        ref_path = create_test_image(tmp, "ref.png")
        tgt_path = create_shifted_image(tmp, ref_path)

        create_resp = client.post(
            f"/api/v1/registrations/project/{project_id}",
            json={
                "name": "CP Test",
                "reference_path": str(ref_path),
                "target_path": str(tgt_path),
            },
        )
        reg_id = create_resp.json()["id"]

        # Create
        cp_resp = client.post(
            f"/api/v1/registrations/{reg_id}/control-points",
            json={
                "ref_x": 10.0,
                "ref_y": 20.0,
                "target_x": 15.0,
                "target_y": 23.0,
            },
        )
        assert cp_resp.status_code == 201
        cp_id = cp_resp.json()["id"]

        # List
        list_resp = client.get(
            f"/api/v1/registrations/{reg_id}/control-points"
        )
        assert list_resp.status_code == 200
        assert len(list_resp.json()) >= 1

        # Move
        move_resp = client.patch(
            f"/api/v1/registrations/{reg_id}/control-points/{cp_id}",
            json={
                "ref_x": 30.0,
                "ref_y": 40.0,
                "target_x": 35.0,
                "target_y": 43.0,
            },
        )
        assert move_resp.status_code == 200
        assert move_resp.json()["ref_x"] == 30.0

        # Delete
        del_resp = client.delete(
            f"/api/v1/registrations/{reg_id}/control-points/{cp_id}"
        )
        assert del_resp.status_code == 204

    def test_bulk_create_control_points(self):
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        ref_path = create_test_image(tmp, "ref.png")
        tgt_path = create_shifted_image(tmp, ref_path)

        create_resp = client.post(
            f"/api/v1/registrations/project/{project_id}",
            json={
                "name": "Bulk CP Test",
                "reference_path": str(ref_path),
                "target_path": str(tgt_path),
            },
        )
        reg_id = create_resp.json()["id"]

        response = client.post(
            f"/api/v1/registrations/{reg_id}/control-points/bulk",
            json={
                "points": [
                    {"ref_x": 10.0, "ref_y": 20.0, "target_x": 15.0, "target_y": 23.0},
                    {"ref_x": 50.0, "ref_y": 60.0, "target_x": 55.0, "target_y": 63.0},
                    {"ref_x": 80.0, "ref_y": 90.0, "target_x": 85.0, "target_y": 93.0},
                ]
            },
        )
        assert response.status_code == 201
        assert len(response.json()) == 3

    def test_history_api(self):
        project_id = get_test_project()
        response = client.get(
            f"/api/v1/registrations/project/{project_id}/history"
        )
        assert response.status_code == 200

    def test_metrics_api(self):
        project_id = get_test_project()
        tmp = Path(tempfile.mkdtemp())
        ref_path = create_test_image(tmp, "ref.png")
        tgt_path = create_shifted_image(tmp, ref_path)

        create_resp = client.post(
            f"/api/v1/registrations/project/{project_id}",
            json={
                "name": "Metrics Test",
                "reference_path": str(ref_path),
                "target_path": str(tgt_path),
            },
        )
        reg_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/registrations/{reg_id}/metrics")
        assert response.status_code == 200
