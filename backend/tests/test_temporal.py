"""Tests for Temporal Engine."""

import uuid

from fastapi.testclient import TestClient

from data_engine.database.datasets import Dataset
from database.connection import SessionLocal
from main import app

client = TestClient(app)


def get_test_project() -> str:
    """Create a test project and return its ID."""
    response = client.post(
        "/api/v1/projects",
        json={"name": f"Temporal Test Project {uuid.uuid4().hex[:8]}"},
    )
    assert response.status_code in (200, 201), f"Failed to create project: {response.status_code} {response.text}"
    return response.json()["id"]


def create_test_dataset(project_id: str) -> str:
    """Create a test dataset directly in the DB and return its ID."""
    db = SessionLocal()
    try:
        ds_id = str(uuid.uuid4())
        ds = Dataset(
            id=ds_id,
            project_id=project_id,
            name=f"Test Dataset {uuid.uuid4().hex[:8]}",
            dataset_type="raster",
            original_filename=f"test_{uuid.uuid4().hex[:8]}.tif",
            internal_filename=f"test_{uuid.uuid4().hex[:8]}.tif",
            extension=".tif",
            file_size=1024,
            checksum=uuid.uuid4().hex,
            storage_path=f"storage/projects/{project_id}/datasets/{ds_id}",
        )
        db.add(ds)
        db.commit()
        return ds_id
    finally:
        db.close()


def test_create_timeline():
    r = client.post("/api/v1/timelines", json={
        "name": f"Test Timeline {uuid.uuid4().hex[:8]}",
        "description": "A test timeline",
        "group_by": "date",
        "sort_order": "asc",
        "tags": ["test", "temporal"],
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"].startswith("Test Timeline")
    assert data["group_by"] == "date"
    assert data["entry_count"] == 0


def test_create_timeline_with_project():
    pid = get_test_project()
    r = client.post("/api/v1/timelines", json={
        "name": f"Project Timeline {uuid.uuid4().hex[:8]}",
        "project_id": pid,
    })
    assert r.status_code == 201
    assert r.json()["project_id"] == pid


def test_list_timelines():
    client.post("/api/v1/timelines", json={"name": f"List TL {uuid.uuid4().hex[:8]}"})
    client.post("/api/v1/timelines", json={"name": f"List TL 2 {uuid.uuid4().hex[:8]}"})
    r = client.get("/api/v1/timelines")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 2
    assert len(data["timelines"]) >= 2


def test_get_timeline():
    r = client.post("/api/v1/timelines", json={"name": f"Get TL {uuid.uuid4().hex[:8]}"})
    tid = r.json()["id"]
    r = client.get(f"/api/v1/timelines/{tid}")
    assert r.status_code == 200
    assert r.json()["id"] == tid


def test_get_timeline_not_found():
    r = client.get("/api/v1/timelines/nonexistent")
    assert r.status_code == 404


def test_update_timeline():
    r = client.post("/api/v1/timelines", json={"name": f"Update TL {uuid.uuid4().hex[:8]}"})
    tid = r.json()["id"]
    r = client.put(f"/api/v1/timelines/{tid}", json={"name": "Updated Timeline"})
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Timeline"


def test_delete_timeline():
    r = client.post("/api/v1/timelines", json={"name": f"Delete TL {uuid.uuid4().hex[:8]}"})
    tid = r.json()["id"]
    r = client.delete(f"/api/v1/timelines/{tid}")
    assert r.status_code == 200
    r = client.get(f"/api/v1/timelines/{tid}")
    assert r.status_code == 404


def test_duplicate_timeline():
    r = client.post("/api/v1/timelines", json={"name": f"Original TL {uuid.uuid4().hex[:8]}"})
    tid = r.json()["id"]
    r = client.post(f"/api/v1/timelines/{tid}/duplicate?name=Duped Timeline")
    assert r.status_code == 201
    assert r.json()["name"] == "Duped Timeline"


def test_toggle_favorite():
    r = client.post("/api/v1/timelines", json={"name": f"Fav TL {uuid.uuid4().hex[:8]}"})
    tid = r.json()["id"]
    r = client.post(f"/api/v1/timelines/{tid}/favorite")
    assert r.status_code == 200
    assert r.json()["favorite"] is True
    r = client.post(f"/api/v1/timelines/{tid}/favorite")
    assert r.json()["favorite"] is False


def test_search_timelines():
    name = f"Searchable TL {uuid.uuid4().hex[:8]}"
    client.post("/api/v1/timelines", json={"name": name})
    r = client.get(f"/api/v1/timelines?search={name[:15]}")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_filter_by_project():
    pid = get_test_project()
    client.post("/api/v1/timelines", json={"name": f"Proj TL {uuid.uuid4().hex[:8]}", "project_id": pid})
    r = client.get(f"/api/v1/timelines?project_id={pid}")
    assert r.status_code == 200


def test_timeline_stats():
    r = client.get("/api/v1/timelines/stats")
    assert r.status_code == 200
    stats = r.json()
    assert "total_timelines" in stats
    assert "total_entries" in stats


def test_add_entry():
    pid = get_test_project()
    ds_id = create_test_dataset(pid)
    r = client.post("/api/v1/timelines", json={"name": f"Entry TL {uuid.uuid4().hex[:8]}"})
    tid = r.json()["id"]
    r = client.post(f"/api/v1/timelines/{tid}/entries", json={
        "dataset_id": ds_id,
        "acquisition_date": "2025-01-15T00:00:00",
        "sensor_name": "SAR-C",
    })
    assert r.status_code == 201
    entry = r.json()
    assert entry["sensor_name"] == "SAR-C"


def test_get_entries():
    pid = get_test_project()
    ds1 = create_test_dataset(pid)
    ds2 = create_test_dataset(pid)
    r = client.post("/api/v1/timelines", json={"name": f"Entries TL {uuid.uuid4().hex[:8]}"})
    tid = r.json()["id"]
    client.post(f"/api/v1/timelines/{tid}/entries", json={"dataset_id": ds1, "acquisition_date": "2025-01-10T00:00:00"})
    client.post(f"/api/v1/timelines/{tid}/entries", json={"dataset_id": ds2, "acquisition_date": "2025-06-20T00:00:00"})
    r = client.get(f"/api/v1/timelines/{tid}/entries")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_entries_sorted_chronologically():
    pid = get_test_project()
    ds1 = create_test_dataset(pid)
    ds2 = create_test_dataset(pid)
    ds3 = create_test_dataset(pid)
    r = client.post("/api/v1/timelines", json={"name": f"Sort TL {uuid.uuid4().hex[:8]}"})
    tid = r.json()["id"]
    client.post(f"/api/v1/timelines/{tid}/entries", json={"dataset_id": ds1, "acquisition_date": "2025-06-01T00:00:00"})
    client.post(f"/api/v1/timelines/{tid}/entries", json={"dataset_id": ds2, "acquisition_date": "2025-01-01T00:00:00"})
    client.post(f"/api/v1/timelines/{tid}/entries", json={"dataset_id": ds3, "acquisition_date": "2025-12-01T00:00:00"})
    r = client.get(f"/api/v1/timelines/{tid}/entries")
    dates = [e["acquisition_date"][:10] for e in r.json()]
    assert dates == sorted(dates)


def test_remove_entry():
    pid = get_test_project()
    ds_id = create_test_dataset(pid)
    r = client.post("/api/v1/timelines", json={"name": f"Remove TL {uuid.uuid4().hex[:8]}"})
    tid = r.json()["id"]
    r = client.post(f"/api/v1/timelines/{tid}/entries", json={"dataset_id": ds_id})
    eid = r.json()["id"]
    r = client.delete(f"/api/v1/timelines/{tid}/entries/{eid}")
    assert r.status_code == 200
    r = client.get(f"/api/v1/timelines/{tid}/entries")
    assert len(r.json()) == 0


def test_create_comparison():
    pid = get_test_project()
    ds1 = create_test_dataset(pid)
    ds2 = create_test_dataset(pid)
    r = client.post("/api/v1/timelines", json={"name": f"Comp TL {uuid.uuid4().hex[:8]}"})
    tid = r.json()["id"]
    r1 = client.post(f"/api/v1/timelines/{tid}/entries", json={"dataset_id": ds1, "acquisition_date": "2025-01-01T00:00:00"})
    r2 = client.post(f"/api/v1/timelines/{tid}/entries", json={"dataset_id": ds2, "acquisition_date": "2025-06-01T00:00:00"})
    r = client.post(f"/api/v1/timelines/{tid}/comparison", json={
        "name": "Test Comparison",
        "mode": "side_by_side",
        "left_entry_id": r1.json()["id"],
        "right_entry_id": r2.json()["id"],
    })
    assert r.status_code == 201
    comp = r.json()
    assert comp["mode"] == "side_by_side"


def test_update_comparison():
    pid = get_test_project()
    ds1 = create_test_dataset(pid)
    ds2 = create_test_dataset(pid)
    r = client.post("/api/v1/timelines", json={"name": f"Comp TL2 {uuid.uuid4().hex[:8]}"})
    tid = r.json()["id"]
    r1 = client.post(f"/api/v1/timelines/{tid}/entries", json={"dataset_id": ds1, "acquisition_date": "2025-01-01T00:00:00"})
    r2 = client.post(f"/api/v1/timelines/{tid}/entries", json={"dataset_id": ds2, "acquisition_date": "2025-06-01T00:00:00"})
    r = client.post(f"/api/v1/timelines/{tid}/comparison", json={"mode": "side_by_side", "left_entry_id": r1.json()["id"], "right_entry_id": r2.json()["id"]})
    cid = r.json()["id"]
    r = client.put(f"/api/v1/timelines/{tid}/comparison/{cid}", json={"swipe_position": 75.0})
    assert r.status_code == 200
    assert r.json()["swipe_position"] == 75.0


def test_add_bookmark():
    r = client.post("/api/v1/timelines", json={"name": f"Bookmark TL {uuid.uuid4().hex[:8]}"})
    tid = r.json()["id"]
    r = client.post(f"/api/v1/timelines/{tid}/bookmarks", json={
        "label": "Event A",
        "color": "#ff0000",
    })
    assert r.status_code == 201
    assert r.json()["label"] == "Event A"


def test_get_bookmarks():
    r = client.post("/api/v1/timelines", json={"name": f"Bkmk TL {uuid.uuid4().hex[:8]}"})
    tid = r.json()["id"]
    client.post(f"/api/v1/timelines/{tid}/bookmarks", json={"label": "B1"})
    client.post(f"/api/v1/timelines/{tid}/bookmarks", json={"label": "B2"})
    r = client.get(f"/api/v1/timelines/{tid}/bookmarks")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_delete_bookmark():
    r = client.post("/api/v1/timelines", json={"name": f"Del Bkmk TL {uuid.uuid4().hex[:8]}"})
    tid = r.json()["id"]
    r = client.post(f"/api/v1/timelines/{tid}/bookmarks", json={"label": "To Delete"})
    bid = r.json()["id"]
    r = client.delete(f"/api/v1/timelines/{tid}/bookmarks/{bid}")
    assert r.status_code == 200


def test_get_logs():
    pid = get_test_project()
    ds_id = create_test_dataset(pid)
    r = client.post("/api/v1/timelines", json={"name": f"Logs TL {uuid.uuid4().hex[:8]}"})
    tid = r.json()["id"]
    client.post(f"/api/v1/timelines/{tid}/entries", json={"dataset_id": ds_id})
    r = client.get(f"/api/v1/timelines/{tid}/logs")
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_get_sensors():
    pid = get_test_project()
    ds1 = create_test_dataset(pid)
    ds2 = create_test_dataset(pid)
    ds3 = create_test_dataset(pid)
    r = client.post("/api/v1/timelines", json={"name": f"Sensors TL {uuid.uuid4().hex[:8]}"})
    tid = r.json()["id"]
    client.post(f"/api/v1/timelines/{tid}/entries", json={"dataset_id": ds1, "sensor_name": "SAR-C"})
    client.post(f"/api/v1/timelines/{tid}/entries", json={"dataset_id": ds2, "sensor_name": "Sentinel-2"})
    client.post(f"/api/v1/timelines/{tid}/entries", json={"dataset_id": ds3, "sensor_name": "SAR-C"})
    r = client.get(f"/api/v1/timelines/{tid}/sensors")
    assert r.status_code == 200
    sensors = r.json()["sensors"]
    assert "SAR-C" in sensors
    assert "Sentinel-2" in sensors


def test_entry_timeline_not_found():
    r = client.post("/api/v1/timelines/nonexistent/entries", json={"dataset_id": str(uuid.uuid4())})
    assert r.status_code == 404


def test_bookmark_timeline_not_found():
    r = client.post("/api/v1/timelines/nonexistent/bookmarks", json={"label": "X"})
    assert r.status_code == 404
