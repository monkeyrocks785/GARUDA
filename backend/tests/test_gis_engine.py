"""Tests for the GARUDA GIS Workspace engine (S3).

Covers raster import + on-demand tiling, vector layer features, asset-to-layer
registration, offline basemaps (local XYZ + GeoTIFF), project isolation, and
path-traversal security.
"""

import json
import uuid
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from config.settings import settings
from database.connection import Base, engine
from main import app

Base.metadata.create_all(bind=engine)

client = TestClient(app)

TRANSPARENT_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def make_png_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(__import__("base64").b64decode(TRANSPARENT_PNG))


def get_test_project() -> str:
    response = client.post(
        "/api/v1/projects",
        json={"name": f"GIS Test {uuid.uuid4().hex[:8]}"},
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["id"]


def make_world_geotiff(path: Path) -> Path:
    import rasterio
    from rasterio.crs import CRS
    from rasterio.transform import from_bounds

    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 128, 128
    transform = from_bounds(-180.0, -80.0, 180.0, 80.0, width, height)
    data = np.random.rand(1, height, width).astype(np.float32) * 255
    data[data < 20] = -9999

    with rasterio.open(
        path,
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
    return path


def make_geojson_file(path: Path, feature_count: int = 3) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    features = []
    for i in range(feature_count):
        features.append(
            {
                "type": "Feature",
                "properties": {"name": f"point-{i}", "value": i},
                "geometry": {
                    "type": "Point",
                    "coordinates": [77.0 + i * 0.1, 28.0 + i * 0.1],
                },
            }
        )
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    return path


# ============================================================
# Raster import + tiles
# ============================================================


def test_import_raster_creates_layer_and_tile_url():
    project_id = get_test_project()
    tmp = Path(settings.TEMP_DIR) / f"gis_{uuid.uuid4().hex[:8]}.tif"
    make_world_geotiff(tmp)

    try:
        with open(tmp, "rb") as f:
            response = client.post(
                f"/api/v1/rasters/{project_id}/import",
                files={"file": ("world.tif", f, "image/tiff")},
            )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["layer_id"]
        assert body["raster_id"] == body["layer_id"] or body["raster_id"]
        assert body["tile_url_template"].endswith("{z}/{x}/{y}.png")
        assert body["crs"] == "EPSG:4326"
        assert body["band_count"] == 1

        layer = client.get(f"/api/v1/projects/{project_id}/layers/{body['layer_id']}")
        assert layer.status_code == 200
        assert layer.json()["layer_type"] == "raster"
        assert layer.json()["crs"] == "EPSG:4326"
    finally:
        tmp.unlink(missing_ok=True)


def test_raster_import_rejects_unsupported_extension():
    project_id = get_test_project()
    response = client.post(
        f"/api/v1/rasters/{project_id}/import",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported raster type" in response.json()["detail"]


def test_raster_tile_serving_and_cache():
    project_id = get_test_project()
    tmp = Path(settings.TEMP_DIR) / f"gis_{uuid.uuid4().hex[:8]}.tif"
    make_world_geotiff(tmp)

    try:
        with open(tmp, "rb") as f:
            imported = client.post(
                f"/api/v1/rasters/{project_id}/import",
                files={"file": ("world.tif", f, "image/tiff")},
            ).json()
        raster_id = imported["raster_id"]

        # z=0 covers the whole world, so the raster intersects it.
        tile = client.get(
            f"/api/v1/rasters/{project_id}/{raster_id}/tiles/0/0/0.png"
        )
        assert tile.status_code == 200, tile.text
        assert tile.headers["content-type"] == "image/png"
        assert tile.content[:8] == b"\x89PNG\r\n\x1a\n"

        # Served from cache on second call.
        tile2 = client.get(
            f"/api/v1/rasters/{project_id}/{raster_id}/tiles/0/0/0.png"
        )
        assert tile2.status_code == 200
        assert tile2.content == tile.content
    finally:
        tmp.unlink(missing_ok=True)


def test_raster_tile_invalid_coordinates():
    project_id = get_test_project()
    tmp = Path(settings.TEMP_DIR) / f"gis_{uuid.uuid4().hex[:8]}.tif"
    make_world_geotiff(tmp)

    try:
        with open(tmp, "rb") as f:
            imported = client.post(
                f"/api/v1/rasters/{project_id}/import",
                files={"file": ("world.tif", f, "image/tiff")},
            ).json()
        raster_id = imported["raster_id"]
        assert (
            client.get(
                f"/api/v1/rasters/{project_id}/{raster_id}/tiles/99/0/0.png"
            ).status_code
            == 400
        )
        assert (
            client.get(
                f"/api/v1/rasters/{project_id}/{raster_id}/tiles/0/999/0.png"
            ).status_code
            == 400
        )
    finally:
        tmp.unlink(missing_ok=True)


def test_raster_tile_project_isolation():
    project_a = get_test_project()
    project_b = get_test_project()
    tmp = Path(settings.TEMP_DIR) / f"gis_{uuid.uuid4().hex[:8]}.tif"
    make_world_geotiff(tmp)

    try:
        with open(tmp, "rb") as f:
            imported = client.post(
                f"/api/v1/rasters/{project_a}/import",
                files={"file": ("world.tif", f, "image/tiff")},
            ).json()
        raster_id = imported["raster_id"]
        assert (
            client.get(
                f"/api/v1/rasters/{project_b}/{raster_id}/tiles/0/0/0.png"
            ).status_code
            == 404
        )
    finally:
        tmp.unlink(missing_ok=True)


# ============================================================
# Vector layer features
# ============================================================


def test_layer_features_for_imported_geojson():
    project_id = get_test_project()
    tmp = Path(settings.TEMP_DIR) / f"gis_{uuid.uuid4().hex[:8]}.geojson"
    make_geojson_file(tmp, feature_count=5)

    try:
        with open(tmp, "rb") as f:
            imported = client.post(
                f"/api/v1/projects/{project_id}/import/geojson",
                files={"file": ("points.geojson", f, "application/geo+json")},
            )
        assert imported.status_code == 201, imported.text
        layer_id = imported.json()["layer_id"]

        response = client.get(
            f"/api/v1/projects/{project_id}/layers/{layer_id}/features"
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["type"] == "FeatureCollection"
        assert len(body["features"]) == 5
        assert body["crs"] == "EPSG:4326"
    finally:
        tmp.unlink(missing_ok=True)


def test_layer_features_caps_feature_count():
    project_id = get_test_project()
    tmp = Path(settings.TEMP_DIR) / f"gis_{uuid.uuid4().hex[:8]}.geojson"
    make_geojson_file(tmp, feature_count=20)

    try:
        with open(tmp, "rb") as f:
            imported = client.post(
                f"/api/v1/projects/{project_id}/import/geojson",
                files={"file": ("points.geojson", f, "application/geo+json")},
            ).json()
        layer_id = imported["layer_id"]

        response = client.get(
            f"/api/v1/projects/{project_id}/layers/{layer_id}/features",
            params={"max_features": 5},
        )
        assert response.status_code == 200
        assert len(response.json()["features"]) <= 5
    finally:
        tmp.unlink(missing_ok=True)


def test_layer_features_rejects_raster_layer():
    project_id = get_test_project()
    tmp = Path(settings.TEMP_DIR) / f"gis_{uuid.uuid4().hex[:8]}.tif"
    make_world_geotiff(tmp)

    try:
        with open(tmp, "rb") as f:
            imported = client.post(
                f"/api/v1/rasters/{project_id}/import",
                files={"file": ("world.tif", f, "image/tiff")},
            ).json()
        response = client.get(
            f"/api/v1/projects/{project_id}/layers/{imported['layer_id']}/features"
        )
        assert response.status_code == 400
    finally:
        tmp.unlink(missing_ok=True)


def test_layer_features_unknown_layer():
    project_id = get_test_project()
    response = client.get(
        f"/api/v1/projects/{project_id}/layers/{uuid.uuid4()}/features"
    )
    assert response.status_code == 404


# ============================================================
# Asset-to-layer registration
# ============================================================


def _create_asset(db_session, project_id, name, path, ext):
    from assets.database.assets import Asset

    asset = Asset(
        id=str(uuid.uuid4()),
        project_id=project_id,
        name=name,
        asset_type="raster" if ext in (".tif", ".tiff") else "vector",
        extension=ext.lstrip("."),
        storage_path=str(path),
        file_size=path.stat().st_size,
        checksum=str(uuid.uuid4()),
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def test_register_raster_asset_as_layer(db_session):
    project_id = get_test_project()
    fixture = Path(settings.BASEMAPS_DIR) / f"asset_{uuid.uuid4().hex[:8]}.tif"
    make_world_geotiff(fixture)
    asset = _create_asset(db_session, project_id, "my tif", fixture, ".tif")

    try:
        response = client.post(
            f"/api/v1/projects/{project_id}/layers/from-asset",
            json={"asset_id": asset.id},
        )
        assert response.status_code == 201, response.text
        layer = response.json()
        assert layer["layer_type"] == "raster"
        assert layer["source_type"] == "raster_metadata"

        # Tile serving works for the asset-backed layer.
        tile = client.get(
            f"/api/v1/rasters/{project_id}/{layer['source_id']}/tiles/0/0/0.png"
        )
        assert tile.status_code == 200
    finally:
        fixture.unlink(missing_ok=True)


def test_register_vector_asset_as_layer(db_session):
    project_id = get_test_project()
    fixture = Path(settings.STORAGE_DIR) / f"asset_{uuid.uuid4().hex[:8]}.geojson"
    make_geojson_file(fixture, feature_count=2)
    asset = _create_asset(db_session, project_id, "my geojson", fixture, ".geojson")

    try:
        response = client.post(
            f"/api/v1/projects/{project_id}/layers/from-asset",
            json={"asset_id": asset.id},
        )
        assert response.status_code == 201, response.text
        layer = response.json()
        assert layer["layer_type"] == "vector"
        assert layer["source_type"] == "asset"

        features = client.get(
            f"/api/v1/projects/{project_id}/layers/{layer['id']}/features"
        )
        assert features.status_code == 200
        assert len(features.json()["features"]) == 2
    finally:
        fixture.unlink(missing_ok=True)


def test_register_asset_unsupported_extension(db_session):
    project_id = get_test_project()
    fixture = Path(settings.STORAGE_DIR) / f"asset_{uuid.uuid4().hex[:8]}.txt"
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_text("hello")
    asset = _create_asset(db_session, project_id, "notes", fixture, ".txt")

    try:
        response = client.post(
            f"/api/v1/projects/{project_id}/layers/from-asset",
            json={"asset_id": asset.id},
        )
        assert response.status_code == 400
    finally:
        fixture.unlink(missing_ok=True)


def test_register_missing_asset():
    project_id = get_test_project()
    response = client.post(
        f"/api/v1/projects/{project_id}/layers/from-asset",
        json={"asset_id": str(uuid.uuid4())},
    )
    assert response.status_code == 400
    assert "Asset not found" in response.json()["detail"]


# ============================================================
# Offline basemaps
# ============================================================


def test_basemap_list_always_contains_blank_grid():
    response = client.get("/api/v1/gis/basemaps")
    assert response.status_code == 200
    ids = [b["id"] for b in response.json()]
    assert "blank_grid" in ids


def test_local_xyz_basemap_discovery_and_tile_serving():
    folder = Path(settings.TILES_DIR) / f"map_{uuid.uuid4().hex[:8]}"
    make_png_file(folder / "1" / "0" / "0.png")

    try:
        response = client.get("/api/v1/gis/basemaps")
        assert response.status_code == 200
        basemaps = response.json()
        xyz = [b for b in basemaps if b["basemap_type"] == "xyz_dir"]
        assert len(xyz) >= 1
        found = next(
            (b for b in xyz if b["name"] == folder.name), None
        )
        assert found, f"Expected basemap {folder.name} in {[b['name'] for b in xyz]}"

        tile = client.get(
            f"/api/v1/gis/basemaps/{found['id']}/tiles/1/0/0.png"
        )
        assert tile.status_code == 200
        assert tile.content[:8] == b"\x89PNG\r\n\x1a\n"
    finally:
        import shutil

        shutil.rmtree(folder, ignore_errors=True)


def test_local_xyz_basemap_missing_tile_404():
    folder = Path(settings.TILES_DIR) / f"map_{uuid.uuid4().hex[:8]}"
    make_png_file(folder / "1" / "0" / "0.png")

    try:
        basemaps = client.get("/api/v1/gis/basemaps").json()
        xyz = next(b for b in basemaps if b["name"] == folder.name)
        assert (
            client.get(f"/api/v1/gis/basemaps/{xyz['id']}/tiles/5/5/5.png").status_code
            == 404
        )
    finally:
        import shutil

        shutil.rmtree(folder, ignore_errors=True)


def test_geotiff_basemap_register_and_tile():
    fixture = Path(settings.BASEMAPS_DIR) / f"base_{uuid.uuid4().hex[:8]}.tif"
    make_world_geotiff(fixture)

    try:
        response = client.post(
            "/api/v1/gis/basemaps/geotiff",
            json={"name": "Test Basemap", "path": str(fixture)},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["basemap_type"] == "geotiff"

        tile = client.get(
            f"/api/v1/gis/basemaps/{body['id']}/tiles/0/0/0.png"
        )
        assert tile.status_code == 200
        assert tile.content[:8] == b"\x89PNG\r\n\x1a\n"
    finally:
        fixture.unlink(missing_ok=True)


def test_geotiff_basemap_rejects_path_outside_storage():
    import tempfile

    outside = Path(tempfile.gettempdir()) / f"outside_{uuid.uuid4().hex[:8]}.tif"
    make_world_geotiff(outside)
    try:
        response = client.post(
            "/api/v1/gis/basemaps/geotiff",
            json={"name": "Evil", "path": str(outside)},
        )
        assert response.status_code == 400
        assert "inside the configured storage" in response.json()["detail"]
    finally:
        outside.unlink(missing_ok=True)


def test_xyz_tile_serving_is_traversal_safe():
    from gis_engine.basemap_service import serve_xyz_tile

    assert serve_xyz_tile("xyz-..%2F..%2Fsecret", 1, 0, 0) is None
    assert serve_xyz_tile("xyz-not-a-folder", 1, 0, 0) is None


# ============================================================
# Layer CRS round-trip
# ============================================================


def test_layer_crs_round_trip():
    project_id = get_test_project()
    response = client.post(
        f"/api/v1/projects/{project_id}/layers",
        json={
            "name": "utm layer",
            "layer_type": "vector",
            "crs": "EPSG:32643",
        },
    )
    assert response.status_code == 201, response.text
    layer_id = response.json()["id"]

    fetched = client.get(
        f"/api/v1/projects/{project_id}/layers/{layer_id}"
    ).json()
    assert fetched["crs"] == "EPSG:32643"
