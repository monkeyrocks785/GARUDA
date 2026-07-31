"""Tests for the Knowledge Engine."""

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def get_test_project() -> str:
    """Create a test project and return its ID."""
    unique_name = f"Knowledge Test {uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/projects",
        json={
            "name": unique_name,
            "description": "Knowledge engine test project",
        },
    )
    assert r.status_code == 201
    return r.json()["id"]


# ── Config Tests ─────────────────────────────────────────────────────────────

class TestConfig:
    def test_get_config(self):
        r = client.get("/api/v1/knowledge/config")
        assert r.status_code == 200
        data = r.json()
        assert "entity_types" in data
        assert "road" in data["entity_types"]
        assert "event_types" in data
        assert "created" in data["event_types"]
        assert "relationship_types" in data
        assert "connected_to" in data["relationship_types"]


# ── Entity CRUD Tests ───────────────────────────────────────────────────────

class TestEntityCRUD:
    def test_create_entity(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={
                "entity_type": "building",
                "name": "BLD-001",
                "description": "Test building",
                "confidence": 0.95,
                "tags": ["test", "building"],
            },
        )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "BLD-001"
        assert data["entity_type"] == "building"
        assert data["confidence"] == 0.95
        assert data["status"] == "active"

    def test_create_entity_invalid_type(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "invalid_type", "name": "Bad Entity"},
        )
        assert r.status_code == 400

    def test_get_entity(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "road", "name": "RD-001"},
        )
        entity_id = r.json()["id"]
        r = client.get(f"/api/v1/knowledge/entities/{entity_id}")
        assert r.status_code == 200
        assert r.json()["name"] == "RD-001"

    def test_get_entity_not_found(self):
        r = client.get(f"/api/v1/knowledge/entities/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_list_entities(self):
        pid = get_test_project()
        client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "BLD-A"},
        )
        client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "road", "name": "RD-A"},
        )
        r = client.get(f"/api/v1/knowledge/project/{pid}/entities")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_list_entities_by_type(self):
        pid = get_test_project()
        client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "B1"},
        )
        client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "road", "name": "R1"},
        )
        r = client.get(
            f"/api/v1/knowledge/project/{pid}/entities",
            params={"entity_type": "building"},
        )
        assert r.status_code == 200
        assert r.json()["total"] == 1
        assert r.json()["items"][0]["entity_type"] == "building"

    def test_list_entities_search(self):
        pid = get_test_project()
        client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "Main Terminal"},
        )
        client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "Storage Shed"},
        )
        r = client.get(
            f"/api/v1/knowledge/project/{pid}/entities",
            params={"search": "Terminal"},
        )
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_update_entity(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "bridge", "name": "BRG-001"},
        )
        entity_id = r.json()["id"]
        r = client.put(
            f"/api/v1/knowledge/entities/{entity_id}",
            json={"name": "BRG-001-Updated", "analyst_notes": "Updated by analyst"},
        )
        assert r.status_code == 200
        assert r.json()["name"] == "BRG-001-Updated"
        assert r.json()["analyst_notes"] == "Updated by analyst"

    def test_update_entity_favorite(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "port", "name": "PT-001"},
        )
        entity_id = r.json()["id"]
        r = client.put(
            f"/api/v1/knowledge/entities/{entity_id}",
            json={"favorite": True},
        )
        assert r.status_code == 200
        assert r.json()["favorite"] is True

    def test_delete_entity(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "tunnel", "name": "TNL-001"},
        )
        entity_id = r.json()["id"]
        r = client.delete(f"/api/v1/knowledge/entities/{entity_id}")
        assert r.status_code == 204
        # Verify deleted
        r = client.get(f"/api/v1/knowledge/entities/{entity_id}")
        assert r.status_code == 404

    def test_create_entity_with_geometry(self):
        pid = get_test_project()
        geometry = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
        }
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={
                "entity_type": "settlement",
                "name": "Settlement Alpha",
                "geometry_json": json.dumps(geometry),
                "bbox": [0.0, 0.0, 10.0, 10.0],
                "centroid": [5.0, 5.0],
            },
        )
        assert r.status_code == 201
        data = r.json()
        assert data["geometry_json"] is not None
        assert data["bbox"] == [0.0, 0.0, 10.0, 10.0]
        assert data["centroid"] == [5.0, 5.0]


# ── Observation Tests ───────────────────────────────────────────────────────

class TestObservations:
    def test_add_observation(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "BLD-OBS"},
        )
        entity_id = r.json()["id"]
        r = client.post(
            f"/api/v1/knowledge/entities/{entity_id}/observations",
            json={
                "observation_type": "detection",
                "source_type": "intelligence_engine",
                "confidence": 0.88,
            },
        )
        assert r.status_code == 201
        data = r.json()
        assert data["observation_type"] == "detection"
        assert data["confidence"] == 0.88

    def test_list_observations(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "road", "name": "RD-OBS"},
        )
        entity_id = r.json()["id"]
        client.post(
            f"/api/v1/knowledge/entities/{entity_id}/observations",
            json={"observation_type": "detection"},
        )
        client.post(
            f"/api/v1/knowledge/entities/{entity_id}/observations",
            json={"observation_type": "measurement"},
        )
        r = client.get(f"/api/v1/knowledge/entities/{entity_id}/observations")
        assert r.status_code == 200
        assert r.json()["total"] == 2

    def test_observation_updates_entity_counts(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "airfield", "name": "AF-OBS"},
        )
        entity_id = r.json()["id"]
        client.post(
            f"/api/v1/knowledge/entities/{entity_id}/observations",
            json={"observation_type": "detection"},
        )
        client.post(
            f"/api/v1/knowledge/entities/{entity_id}/observations",
            json={"observation_type": "measurement"},
        )
        r = client.get(f"/api/v1/knowledge/entities/{entity_id}")
        assert r.json()["observation_count"] == 2
        assert r.json()["first_observed_at"] is not None
        assert r.json()["last_observed_at"] is not None

    def test_add_observation_to_nonexistent_entity(self):
        r = client.post(
            f"/api/v1/knowledge/entities/{uuid.uuid4()}/observations",
            json={"observation_type": "detection"},
        )
        assert r.status_code == 404


# ── Relationship Tests ──────────────────────────────────────────────────────

class TestRelationships:
    def _create_two_entities(self, pid):
        r1 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "BLD-REL"},
        )
        r2 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "road", "name": "RD-REL"},
        )
        return r1.json()["id"], r2.json()["id"]

    def test_create_relationship(self):
        pid = get_test_project()
        eid1, eid2 = self._create_two_entities(pid)
        r = client.post(
            "/api/v1/knowledge/relationships",
            json={
                "source_entity_id": eid1,
                "target_entity_id": eid2,
                "relationship_type": "connected_to",
                "confidence": 0.9,
            },
        )
        assert r.status_code == 201
        data = r.json()
        assert data["relationship_type"] == "connected_to"
        assert data["confidence"] == 0.9

    def test_create_relationship_invalid_type(self):
        pid = get_test_project()
        eid1, eid2 = self._create_two_entities(pid)
        r = client.post(
            "/api/v1/knowledge/relationships",
            json={
                "source_entity_id": eid1,
                "target_entity_id": eid2,
                "relationship_type": "invalid_type",
            },
        )
        assert r.status_code == 400

    def test_create_relationship_nonexistent_entity(self):
        pid = get_test_project()
        eid, _ = self._create_two_entities(pid)
        r = client.post(
            "/api/v1/knowledge/relationships",
            json={
                "source_entity_id": eid,
                "target_entity_id": str(uuid.uuid4()),
                "relationship_type": "connected_to",
            },
        )
        assert r.status_code == 400

    def test_create_self_relationship(self):
        pid = get_test_project()
        eid, _ = self._create_two_entities(pid)
        r = client.post(
            "/api/v1/knowledge/relationships",
            json={
                "source_entity_id": eid,
                "target_entity_id": eid,
                "relationship_type": "connected_to",
            },
        )
        assert r.status_code == 400

    def test_list_relationships(self):
        pid = get_test_project()
        eid1, eid2 = self._create_two_entities(pid)
        client.post(
            "/api/v1/knowledge/relationships",
            json={
                "source_entity_id": eid1,
                "target_entity_id": eid2,
                "relationship_type": "connected_to",
            },
        )
        r = client.get(f"/api/v1/knowledge/project/{pid}/relationships")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_list_relationships_by_entity(self):
        pid = get_test_project()
        eid1, eid2 = self._create_two_entities(pid)
        client.post(
            "/api/v1/knowledge/relationships",
            json={
                "source_entity_id": eid1,
                "target_entity_id": eid2,
                "relationship_type": "connected_to",
            },
        )
        r = client.get(
            f"/api/v1/knowledge/project/{pid}/relationships",
            params={"entity_id": eid1},
        )
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_get_entity_neighbors(self):
        pid = get_test_project()
        eid1, eid2 = self._create_two_entities(pid)
        client.post(
            "/api/v1/knowledge/relationships",
            json={
                "source_entity_id": eid1,
                "target_entity_id": eid2,
                "relationship_type": "adjacent_to",
            },
        )
        r = client.get(f"/api/v1/knowledge/entities/{eid1}/neighbors")
        assert r.status_code == 200
        neighbors = r.json()
        assert len(neighbors) == 1
        assert neighbors[0]["entity"]["id"] == eid2
        assert neighbors[0]["direction"] == "outgoing"

    def test_delete_relationship(self):
        pid = get_test_project()
        eid1, eid2 = self._create_two_entities(pid)
        r = client.post(
            "/api/v1/knowledge/relationships",
            json={
                "source_entity_id": eid1,
                "target_entity_id": eid2,
                "relationship_type": "crosses",
            },
        )
        rel_id = r.json()["id"]
        r = client.delete(f"/api/v1/knowledge/relationships/{rel_id}")
        assert r.status_code == 204

    def test_update_relationship(self):
        pid = get_test_project()
        eid1, eid2 = self._create_two_entities(pid)
        r = client.post(
            "/api/v1/knowledge/relationships",
            json={
                "source_entity_id": eid1,
                "target_entity_id": eid2,
                "relationship_type": "connected_to",
            },
        )
        rel_id = r.json()["id"]
        r = client.put(
            f"/api/v1/knowledge/relationships/{rel_id}",
            json={"confidence": 0.75, "description": "Updated relationship"},
        )
        assert r.status_code == 200
        assert r.json()["confidence"] == 0.75
        assert r.json()["description"] == "Updated relationship"


# ── Event Tests ──────────────────────────────────────────────────────────────

class TestEvents:
    def test_create_event(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "river", "name": "RVR-001"},
        )
        entity_id = r.json()["id"]
        r = client.post(
            "/api/v1/knowledge/events",
            json={
                "entity_id": entity_id,
                "event_type": "observed",
                "description": "River observed from satellite",
                "confidence": 0.92,
            },
        )
        assert r.status_code == 201
        data = r.json()
        assert data["event_type"] == "observed"
        assert data["confidence"] == 0.92

    def test_create_event_invalid_type(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "vegetation", "name": "VEG-001"},
        )
        entity_id = r.json()["id"]
        r = client.post(
            "/api/v1/knowledge/events",
            json={
                "entity_id": entity_id,
                "event_type": "invalid_event",
            },
        )
        assert r.status_code == 400

    def test_list_entity_events(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "railway", "name": "RY-001"},
        )
        entity_id = r.json()["id"]
        client.post(
            "/api/v1/knowledge/events",
            json={"entity_id": entity_id, "event_type": "created"},
        )
        client.post(
            "/api/v1/knowledge/events",
            json={"entity_id": entity_id, "event_type": "observed"},
        )
        r = client.get(f"/api/v1/knowledge/entities/{entity_id}/events")
        assert r.status_code == 200
        assert r.json()["total"] == 2

    def test_list_project_events(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "bridge", "name": "BRG-EVT"},
        )
        entity_id = r.json()["id"]
        client.post(
            "/api/v1/knowledge/events",
            json={"entity_id": entity_id, "event_type": "created"},
        )
        r = client.get(f"/api/v1/knowledge/project/{pid}/events")
        assert r.status_code == 200
        assert r.json()["total"] == 1
        assert r.json()["items"][0]["entity_name"] == "BRG-EVT"

    def test_delete_event(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "BLD-EVT"},
        )
        entity_id = r.json()["id"]
        r = client.post(
            "/api/v1/knowledge/events",
            json={"entity_id": entity_id, "event_type": "expanded"},
        )
        event_id = r.json()["id"]
        r = client.delete(f"/api/v1/knowledge/events/{event_id}")
        assert r.status_code == 204


# ── History Tests ────────────────────────────────────────────────────────────

class TestHistory:
    def test_entity_creation_recorded_in_history(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "BLD-HIST"},
        )
        entity_id = r.json()["id"]
        r = client.get(f"/api/v1/knowledge/entities/{entity_id}/history")
        assert r.status_code == 200
        assert r.json()["total"] >= 1
        assert r.json()["items"][0]["change_type"] == "created"

    def test_update_recorded_in_history(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "road", "name": "RD-HIST"},
        )
        entity_id = r.json()["id"]
        client.put(
            f"/api/v1/knowledge/entities/{entity_id}",
            json={"name": "RD-HIST-Updated"},
        )
        r = client.get(f"/api/v1/knowledge/entities/{entity_id}/history")
        assert r.status_code == 200
        change_types = [h["change_type"] for h in r.json()["items"]]
        assert "updated" in change_types

    def test_history_summary(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "port", "name": "PT-HIST"},
        )
        entity_id = r.json()["id"]
        client.put(
            f"/api/v1/knowledge/entities/{entity_id}",
            json={"name": "PT-HIST-v2"},
        )
        r = client.get(f"/api/v1/knowledge/entities/{entity_id}/history/summary")
        assert r.status_code == 200
        data = r.json()
        assert data["total_changes"] >= 2
        assert "created" in data["change_counts"]
        assert "updated" in data["change_counts"]


# ── Graph Tests ──────────────────────────────────────────────────────────────

class TestGraph:
    def test_get_entity_graph(self):
        pid = get_test_project()
        r1 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "G-BLD"},
        )
        r2 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "road", "name": "G-RD"},
        )
        eid1, eid2 = r1.json()["id"], r2.json()["id"]
        client.post(
            "/api/v1/knowledge/relationships",
            json={
                "source_entity_id": eid1,
                "target_entity_id": eid2,
                "relationship_type": "connected_to",
            },
        )
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/graph",
            json={},
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

    def test_get_subgraph(self):
        pid = get_test_project()
        r1 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "SG-B1"},
        )
        r2 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "road", "name": "SG-R1"},
        )
        r3 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "bridge", "name": "SG-BRG"},
        )
        eid1, eid2, eid3 = r1.json()["id"], r2.json()["id"], r3.json()["id"]
        client.post(
            "/api/v1/knowledge/relationships",
            json={
                "source_entity_id": eid1,
                "target_entity_id": eid2,
                "relationship_type": "connected_to",
            },
        )
        client.post(
            "/api/v1/knowledge/relationships",
            json={
                "source_entity_id": eid2,
                "target_entity_id": eid3,
                "relationship_type": "crosses",
            },
        )
        # Get subgraph around eid2 (connected to both)
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/graph",
            json={"entity_id": eid2, "depth": 1},
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data["nodes"]) == 3
        assert len(data["edges"]) == 2

    def test_get_connected_components(self):
        pid = get_test_project()
        r1 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "CC-B1"},
        )
        r2 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "road", "name": "CC-R1"},
        )
        r3 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "bridge", "name": "CC-BRG"},
        )
        eid1, eid2, eid3 = r1.json()["id"], r2.json()["id"], r3.json()["id"]
        # Connect B1-R1 (component 1)
        client.post(
            "/api/v1/knowledge/relationships",
            json={
                "source_entity_id": eid1,
                "target_entity_id": eid2,
                "relationship_type": "connected_to",
            },
        )
        # BRG is isolated (component 2)
        r = client.get(f"/api/v1/knowledge/project/{pid}/graph/components")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 2

    def test_entity_degree(self):
        pid = get_test_project()
        r1 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "DEG-B1"},
        )
        r2 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "road", "name": "DEG-R1"},
        )
        r3 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "road", "name": "DEG-R2"},
        )
        eid1, eid2, eid3 = r1.json()["id"], r2.json()["id"], r3.json()["id"]
        client.post(
            "/api/v1/knowledge/relationships",
            json={
                "source_entity_id": eid1,
                "target_entity_id": eid2,
                "relationship_type": "connected_to",
            },
        )
        client.post(
            "/api/v1/knowledge/relationships",
            json={
                "source_entity_id": eid1,
                "target_entity_id": eid3,
                "relationship_type": "adjacent_to",
            },
        )
        r = client.get(f"/api/v1/knowledge/entities/{eid1}/graph/degree")
        assert r.status_code == 200
        data = r.json()
        assert data["outgoing"] == 2
        assert data["total"] == 2


# ── Search Tests ─────────────────────────────────────────────────────────────

class TestSearch:
    def test_search_entities(self):
        pid = get_test_project()
        client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "Main Terminal"},
        )
        client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "road", "name": "Access Road"},
        )
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/search",
            json={"query": "Terminal"},
        )
        assert r.status_code == 200
        assert r.json()["total"] == 1
        assert r.json()["items"][0]["name"] == "Main Terminal"

    def test_search_with_type_filter(self):
        pid = get_test_project()
        client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "Building Alpha"},
        )
        client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "road", "name": "Road Alpha"},
        )
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/search",
            json={"query": "Alpha", "entity_types": ["building"]},
        )
        assert r.status_code == 200
        assert r.json()["total"] == 1
        assert r.json()["items"][0]["entity_type"] == "building"

    def test_search_relationships(self):
        pid = get_test_project()
        r1 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "SR-B1"},
        )
        r2 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "road", "name": "SR-R1"},
        )
        client.post(
            "/api/v1/knowledge/relationships",
            json={
                "source_entity_id": r1.json()["id"],
                "target_entity_id": r2.json()["id"],
                "relationship_type": "connected_to",
            },
        )
        r = client.get(
            f"/api/v1/knowledge/project/{pid}/search/relationships",
            params={"relationship_type": "connected_to"},
        )
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_search_events(self):
        pid = get_test_project()
        r1 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "SE-B1"},
        )
        client.post(
            "/api/v1/knowledge/events",
            json={
                "entity_id": r1.json()["id"],
                "event_type": "expanded",
                "description": "Building expanded significantly",
            },
        )
        r = client.get(
            f"/api/v1/knowledge/project/{pid}/search/events",
            params={"query": "expanded"},
        )
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_get_statistics(self):
        pid = get_test_project()
        r1 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "STAT-B1"},
        )
        r2 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "road", "name": "STAT-R1"},
        )
        client.post(
            "/api/v1/knowledge/relationships",
            json={
                "source_entity_id": r1.json()["id"],
                "target_entity_id": r2.json()["id"],
                "relationship_type": "connected_to",
            },
        )
        client.post(
            "/api/v1/knowledge/events",
            json={
                "entity_id": r1.json()["id"],
                "event_type": "observed",
            },
        )
        r = client.get(f"/api/v1/knowledge/project/{pid}/stats")
        assert r.status_code == 200
        data = r.json()
        assert data["entities"]["total"] == 2
        assert data["relationships"]["total"] == 1
        assert data["events"]["total"] == 1


# ── Persistence Tests ────────────────────────────────────────────────────────

class TestPersistence:
    def test_entity_persists(self):
        pid = get_test_project()
        r = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "tunnel", "name": "TNL-PERSIST"},
        )
        entity_id = r.json()["id"]
        # Verify it can be retrieved
        r = client.get(f"/api/v1/knowledge/entities/{entity_id}")
        assert r.status_code == 200
        assert r.json()["name"] == "TNL-PERSIST"

    def test_relationship_persists(self):
        pid = get_test_project()
        r1 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "building", "name": "P-B1"},
        )
        r2 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "road", "name": "P-R1"},
        )
        r = client.post(
            "/api/v1/knowledge/relationships",
            json={
                "source_entity_id": r1.json()["id"],
                "target_entity_id": r2.json()["id"],
                "relationship_type": "connected_to",
            },
        )
        rel_id = r.json()["id"]
        r = client.get(f"/api/v1/knowledge/relationships/{rel_id}")
        assert r.status_code == 200

    def test_event_persists(self):
        pid = get_test_project()
        r1 = client.post(
            f"/api/v1/knowledge/project/{pid}/entities",
            json={"entity_type": "river", "name": "P-RVR"},
        )
        r = client.post(
            "/api/v1/knowledge/events",
            json={
                "entity_id": r1.json()["id"],
                "event_type": "created",
                "description": "River discovered",
            },
        )
        event_id = r.json()["id"]
        r = client.get(f"/api/v1/knowledge/events/{event_id}")
        assert r.status_code == 200


# ── All Entity Types Tests ──────────────────────────────────────────────────

class TestEntityTypes:
    def test_all_entity_types(self):
        """Test creating an entity for each supported type."""
        pid = get_test_project()
        entity_types = [
            "road", "bridge", "building", "settlement", "river",
            "vegetation", "airfield", "tunnel", "railway", "port", "unknown",
        ]
        for etype in entity_types:
            r = client.post(
                f"/api/v1/knowledge/project/{pid}/entities",
                json={"entity_type": etype, "name": f"Test-{etype}"},
            )
            assert r.status_code == 201, f"Failed for type: {etype}"
            assert r.json()["entity_type"] == etype
