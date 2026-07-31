"""Tests for GARUDA Raster Processing Engine."""

import tempfile
import uuid
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from database.connection import Base, engine
from main import app

Base.metadata.create_all(bind=engine)

client = TestClient(app)


def get_test_project() -> str:
    """Create a test project and return its ID."""
    response = client.post(
        "/api/v1/projects",
        json={"name": f"Raster Test {uuid.uuid4().hex[:8]}"},
    )
    return response.json()["id"]


def create_test_geotiff(tmp_dir: Path, name: str = "test.tif") -> Path:
    """Create a test GeoTIFF file."""
    import rasterio
    from rasterio.crs import CRS
    from rasterio.transform import from_bounds

    file_path = tmp_dir / name
    width, height = 100, 100
    transform = from_bounds(77.0, 28.0, 78.0, 29.0, width, height)

    data = np.random.rand(1, height, width).astype(np.float32) * 100

    with rasterio.open(
        file_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs=CRS.from_epsg(4326),
        transform=transform,
        nodata=-9999,
    ) as dst:
        dst.write(data)

    return file_path


def create_multiband_geotiff(tmp_dir: Path, name: str = "multiband.tif") -> Path:
    """Create a multi-band GeoTIFF."""
    import rasterio
    from rasterio.crs import CRS
    from rasterio.transform import from_bounds

    file_path = tmp_dir / name
    width, height = 50, 50
    transform = from_bounds(77.0, 28.0, 78.0, 29.0, width, height)

    data = np.random.rand(3, height, width).astype(np.float32) * 100

    with rasterio.open(
        file_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=3,
        dtype="float32",
        crs=CRS.from_epsg(4326),
        transform=transform,
    ) as dst:
        dst.write(data)

    return file_path


# ============================================================
# Metadata Tests
# ============================================================


def test_extract_metadata():
    """Test raster metadata extraction."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tif_path = create_test_geotiff(Path(tmp_dir))

        response = client.post(
            f"/api/v1/rasters/{project_id}/metadata",
            params={"file_path": str(tif_path)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["width"] == 100
        assert data["height"] == 100
        assert data["band_count"] == 1
        assert data["crs"] == "EPSG:4326"
        assert data["project_id"] == project_id


def test_list_rasters():
    """Test listing rasters for a project."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tif_path = create_test_geotiff(Path(tmp_dir))

        client.post(
            f"/api/v1/rasters/{project_id}/metadata",
            params={"file_path": str(tif_path)},
        )

        response = client.get(f"/api/v1/rasters/{project_id}/list")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


def test_get_raster_by_id():
    """Test getting raster by ID."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tif_path = create_test_geotiff(Path(tmp_dir))

        create_resp = client.post(
            f"/api/v1/rasters/{project_id}/metadata",
            params={"file_path": str(tif_path)},
        )
        raster_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/rasters/{project_id}/{raster_id}")
        assert response.status_code == 200
        assert response.json()["id"] == raster_id


def test_get_raster_not_found():
    """Test 404 for non-existent raster."""
    project_id = get_test_project()
    response = client.get(f"/api/v1/rasters/{project_id}/nonexistent")
    assert response.status_code == 404


# ============================================================
# Processing Tests
# ============================================================


def test_reproject():
    """Test raster reprojection."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tif_path = create_test_geotiff(Path(tmp_dir))

        create_resp = client.post(
            f"/api/v1/rasters/{project_id}/metadata",
            params={"file_path": str(tif_path)},
        )
        raster_id = create_resp.json()["id"]

        response = client.post(
            f"/api/v1/rasters/{project_id}/{raster_id}/reproject",
            json={"target_crs": "EPSG:32633", "resampling": "nearest"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["target_crs"] == "EPSG:32633"
        assert "width" in data


def test_crop():
    """Test raster cropping."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tif_path = create_test_geotiff(Path(tmp_dir))

        create_resp = client.post(
            f"/api/v1/rasters/{project_id}/metadata",
            params={"file_path": str(tif_path)},
        )
        raster_id = create_resp.json()["id"]

        response = client.post(
            f"/api/v1/rasters/{project_id}/{raster_id}/crop",
            json={"bbox": [77.2, 28.2, 77.8, 28.8]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "width" in data
        assert "height" in data


def test_clip():
    """Test raster clipping with geometry."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tif_path = create_test_geotiff(Path(tmp_dir))

        create_resp = client.post(
            f"/api/v1/rasters/{project_id}/metadata",
            params={"file_path": str(tif_path)},
        )
        raster_id = create_resp.json()["id"]

        geometry = {
            "type": "Polygon",
            "coordinates": [
                [[77.0, 28.0], [78.0, 28.0], [78.0, 29.0], [77.0, 29.0], [77.0, 28.0]]
            ],
        }

        response = client.post(
            f"/api/v1/rasters/{project_id}/{raster_id}/clip",
            json={"geometry": geometry, "all_touched": True},
        )

        assert response.status_code == 200


def test_overview():
    """Test overview pyramid generation."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tif_path = create_test_geotiff(Path(tmp_dir))

        create_resp = client.post(
            f"/api/v1/rasters/{project_id}/metadata",
            params={"file_path": str(tif_path)},
        )
        raster_id = create_resp.json()["id"]

        response = client.post(
            f"/api/v1/rasters/{project_id}/{raster_id}/overview",
            json={"levels": [2, 4, 8], "resampling": "nearest"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["levels"] == [2, 4, 8]


def test_resample():
    """Test raster resampling."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tif_path = create_test_geotiff(Path(tmp_dir))

        create_resp = client.post(
            f"/api/v1/rasters/{project_id}/metadata",
            params={"file_path": str(tif_path)},
        )
        raster_id = create_resp.json()["id"]

        response = client.post(
            f"/api/v1/rasters/{project_id}/{raster_id}/resample",
            json={"target_width": 50, "target_height": 50, "resampling": "nearest"},
        )

        assert response.status_code == 200
        data = response.json()
        assert tuple(data["new_size"]) == (50, 50)


def test_extract_bands():
    """Test band extraction."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tif_path = create_multiband_geotiff(Path(tmp_dir))

        create_resp = client.post(
            f"/api/v1/rasters/{project_id}/metadata",
            params={"file_path": str(tif_path)},
        )
        raster_id = create_resp.json()["id"]

        response = client.post(
            f"/api/v1/rasters/{project_id}/{raster_id}/bands",
            json={"bands": [1, 3]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["extracted_bands"] == [1, 3]


def test_nodata_set():
    """Test setting nodata value."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tif_path = create_test_geotiff(Path(tmp_dir))

        create_resp = client.post(
            f"/api/v1/rasters/{project_id}/metadata",
            params={"file_path": str(tif_path)},
        )
        raster_id = create_resp.json()["id"]

        response = client.post(
            f"/api/v1/rasters/{project_id}/{raster_id}/nodata",
            json={"operation": "set", "nodata_value": -9999},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nodata_value"] == -9999


def test_thumbnail():
    """Test thumbnail generation."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tif_path = create_test_geotiff(Path(tmp_dir))

        create_resp = client.post(
            f"/api/v1/rasters/{project_id}/metadata",
            params={"file_path": str(tif_path)},
        )
        raster_id = create_resp.json()["id"]

        response = client.post(
            f"/api/v1/rasters/{project_id}/{raster_id}/thumbnail",
            params={"width": 128, "height": 128},
        )

        assert response.status_code == 200
        data = response.json()
        assert "width" in data
        assert "height" in data


def test_mosaic():
    """Test raster mosaicking."""
    project_id = get_test_project()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tif1 = create_test_geotiff(Path(tmp_dir), "tile1.tif")
        tif2 = create_test_geotiff(Path(tmp_dir), "tile2.tif")

        response = client.post(
            f"/api/v1/rasters/{project_id}/mosaic",
            json={
                "file_paths": [str(tif1), str(tif2)],
                "output_filename": "mosaic.tif",
                "method": "first",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["input_count"] == 2


def test_processing_history():
    """Test getting processing history."""
    project_id = get_test_project()

    response = client.get(f"/api/v1/rasters/{project_id}/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_derived_products():
    """Test getting derived products."""
    project_id = get_test_project()

    response = client.get(f"/api/v1/rasters/{project_id}/derived")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ============================================================
# Validation Tests
# ============================================================


def test_file_not_found():
    """Test 404 for non-existent file."""
    project_id = get_test_project()
    response = client.post(
        f"/api/v1/rasters/{project_id}/metadata",
        params={"file_path": "/nonexistent/file.tif"},
    )
    assert response.status_code == 404
