"""Tests for geospatial endpoints."""

import json
import shutil
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from database.connection import Base, engine
from main import app

# Create tables for testing
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_create_aoi():
    """Test creating an AOI."""
    # Create a project first
    project_response = client.post(
        "/api/v1/projects",
        json={"name": f"AOI Test Project {uuid.uuid4().hex[:8]}"},
    )
    project_id = project_response.json()["id"]

    # Create AOI
    response = client.post(
        f"/api/v1/projects/{project_id}/aoi",
        json={
            "name": "Test AOI",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [0, 0],
                        [1, 0],
                        [1, 1],
                        [0, 1],
                        [0, 0],
                    ]
                ],
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test AOI"
    assert data["geometry_type"] == "Polygon"

    # Cleanup
    storage_path = Path(project_response.json()["storage_path"])
    shutil.rmtree(storage_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{project_id}")


def test_list_aois():
    """Test listing AOIs for a project."""
    # Create a project first
    project_response = client.post(
        "/api/v1/projects",
        json={"name": f"AOI List Test Project {uuid.uuid4().hex[:8]}"},
    )
    project_id = project_response.json()["id"]

    # List AOIs (should be empty)
    response = client.get(f"/api/v1/projects/{project_id}/aoi")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Cleanup
    storage_path = Path(project_response.json()["storage_path"])
    shutil.rmtree(storage_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{project_id}")


def test_create_layer():
    """Test creating a layer."""
    # Create a project first
    project_response = client.post(
        "/api/v1/projects",
        json={"name": f"Layer Test Project {uuid.uuid4().hex[:8]}"},
    )
    project_id = project_response.json()["id"]

    # Create layer
    response = client.post(
        f"/api/v1/projects/{project_id}/layers",
        json={
            "name": "Test Layer",
            "layer_type": "vector",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Layer"
    assert data["layer_type"] == "vector"
    assert data["visible"] == True

    # Cleanup
    storage_path = Path(project_response.json()["storage_path"])
    shutil.rmtree(storage_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{project_id}")


def test_toggle_layer_visibility():
    """Test toggling layer visibility."""
    # Create a project first
    project_response = client.post(
        "/api/v1/projects",
        json={"name": f"Layer Toggle Test Project {uuid.uuid4().hex[:8]}"},
    )
    project_id = project_response.json()["id"]

    # Create layer
    layer_response = client.post(
        f"/api/v1/projects/{project_id}/layers",
        json={"name": "Toggle Layer", "layer_type": "vector"},
    )
    layer_id = layer_response.json()["id"]

    # Toggle visibility
    response = client.post(
        f"/api/v1/projects/{project_id}/layers/{layer_id}/toggle-visibility"
    )
    assert response.status_code == 200
    assert response.json()["visible"] == False

    # Cleanup
    storage_path = Path(project_response.json()["storage_path"])
    shutil.rmtree(storage_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{project_id}")


def test_import_geojson():
    """Test importing a GeoJSON file."""
    # Create a project first
    project_response = client.post(
        "/api/v1/projects",
        json={"name": f"Import Test Project {uuid.uuid4().hex[:8]}"},
    )
    project_id = project_response.json()["id"]

    # Create GeoJSON content
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [0, 0],
                            [1, 0],
                            [1, 1],
                            [0, 1],
                            [0, 0],
                        ]
                    ],
                },
                "properties": {"name": "Test Feature"},
            }
        ],
    }

    # Import GeoJSON
    response = client.post(
        f"/api/v1/projects/{project_id}/import/geojson",
        files={"file": ("test.geojson", json.dumps(geojson), "application/json")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["file_type"] == "geojson"
    assert data["feature_count"] == 1

    # Cleanup
    storage_path = Path(project_response.json()["storage_path"])
    shutil.rmtree(storage_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{project_id}")


def test_import_kml():
    """Test importing a KML file."""
    # Create a project first
    project_response = client.post(
        "/api/v1/projects",
        json={"name": f"KML Import Test {uuid.uuid4().hex[:8]}"},
    )
    project_id = project_response.json()["id"]

    # Create KML content
    kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Test KML</name>
    <Placemark>
      <name>Test Point</name>
      <Point>
        <coordinates>0,0,0</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>"""

    # Import KML
    response = client.post(
        f"/api/v1/projects/{project_id}/import/kml",
        files={"file": ("test.kml", kml_content, "application/vnd.google-earth.kml+xml")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["file_type"] == "kml"

    # Cleanup
    storage_path = Path(project_response.json()["storage_path"])
    shutil.rmtree(storage_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{project_id}")


def test_map_state():
    """Test saving and loading map state."""
    # Create a project first
    project_response = client.post(
        "/api/v1/projects",
        json={"name": f"Map State Test Project {uuid.uuid4().hex[:8]}"},
    )
    project_id = project_response.json()["id"]

    # Get default map state
    response = client.get(f"/api/v1/projects/{project_id}/map-state")
    assert response.status_code == 200
    data = response.json()
    assert data["zoom"] == 2.0
    assert data["basemap"] == "osm"

    # Update map state
    response = client.put(
        f"/api/v1/projects/{project_id}/map-state",
        json={"zoom": 10.0, "basemap": "esri_satellite"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["zoom"] == 10.0
    assert data["basemap"] == "esri_satellite"

    # Cleanup
    storage_path = Path(project_response.json()["storage_path"])
    shutil.rmtree(storage_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{project_id}")


def test_export_geojson():
    """Test exporting AOIs as GeoJSON."""
    # Create a project first
    project_response = client.post(
        "/api/v1/projects",
        json={"name": f"Export Test Project {uuid.uuid4().hex[:8]}"},
    )
    project_id = project_response.json()["id"]

    # Create AOI
    aoi_response = client.post(
        f"/api/v1/projects/{project_id}/aoi",
        json={
            "name": "Export AOI",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [0, 0],
                        [1, 0],
                        [1, 1],
                        [0, 1],
                        [0, 0],
                    ]
                ],
            },
        },
    )
    aoi_id = aoi_response.json()["id"]

    # Export to GeoJSON
    response = client.post(
        f"/api/v1/projects/{project_id}/export/geojson",
        json={"aoi_ids": [aoi_id], "name": "test_export"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "geojson"
    assert "FeatureCollection" in data["content"]

    # Cleanup
    storage_path = Path(project_response.json()["storage_path"])
    shutil.rmtree(storage_path, ignore_errors=True)
    client.delete(f"/api/v1/projects/{project_id}")
