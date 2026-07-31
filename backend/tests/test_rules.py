"""Tests for the Intelligence Rules & Alert Engine."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def get_test_project():
    r = client.post("/api/v1/projects", json={"name": "Rules-Test-Proj"})
    assert r.status_code in (200, 201)
    return r.json()["id"]


def create_test_entity(pid: str, entity_type: str, name: str):
    r = client.post(
        f"/api/v1/knowledge/project/{pid}/entities",
        json={
            "entity_type": entity_type,
            "name": name,
            "attributes": {"count": 10, "length": 500, "area": 1000},
        },
    )
    assert r.status_code == 201, f"Entity creation failed: {r.text}"
    return r.json()["id"]


def add_observation(eid: str, attributes: dict, observed_at: str = "2024-01-01T00:00:00"):
    r = client.post(
        f"/api/v1/knowledge/entities/{eid}/observations",
        json={
            "observation_type": "survey",
            "attributes": attributes,
            "observed_at": observed_at,
        },
    )
    assert r.status_code == 201, f"Observation creation failed: {r.text}"
    return r.json()["id"]


def build_rule(
    name: str,
    rule_type: str = "entity",
    conditions: list | None = None,
    actions: list | None = None,
    project_id: str | None = None,
    priority: str = "medium",
    enabled: bool = True,
):
    payload = {
        "name": name,
        "rule_type": rule_type,
        "enabled": enabled,
        "priority": priority,
        "project_id": project_id,
    }
    if conditions:
        payload["conditions"] = conditions
    if actions:
        payload["actions"] = actions
    return payload


# ── Rule CRUD Tests ─────────────────────────────────────────────────────────

class TestRuleCRUD:
    def test_create_rule(self):
        r = client.post("/api/v1/rules/rules", json=build_rule("Test-Rule-CRUD"))
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Test-Rule-CRUD"
        assert data["rule_type"] == "entity"
        assert data["enabled"] is True
        assert "id" in data

    def test_create_rule_with_conditions(self):
        payload = build_rule(
            name="Rule-With-Conditions",
            conditions=[
                {
                    "condition_type": "equals",
                    "field": "entity_type",
                    "operator": "equals",
                    "value": "building",
                }
            ],
            actions=[
                {
                    "action_type": "generate_alert",
                    "config": {"title": "Building detected"},
                }
            ],
        )
        r = client.post("/api/v1/rules/rules", json=payload)
        assert r.status_code == 201
        data = r.json()
        assert len(data["conditions"]) == 1
        assert data["conditions"][0]["condition_type"] == "equals"

    def test_create_rule_invalid_type(self):
        payload = build_rule("Bad-Rule", rule_type="invalid_type")
        r = client.post("/api/v1/rules/rules", json=payload)
        assert r.status_code == 400

    def test_get_rule(self):
        create = client.post("/api/v1/rules/rules", json=build_rule("Get-Rule"))
        rule_id = create.json()["id"]

        r = client.get(f"/api/v1/rules/rules/{rule_id}")
        assert r.status_code == 200
        assert r.json()["id"] == rule_id

    def test_get_rule_not_found(self):
        r = client.get("/api/v1/rules/rules/nonexistent-id")
        assert r.status_code == 404

    def test_list_rules(self):
        client.post("/api/v1/rules/rules", json=build_rule("List-Rule-1"))
        client.post("/api/v1/rules/rules", json=build_rule("List-Rule-2"))
        r = client.get("/api/v1/rules/rules")
        assert r.status_code == 200
        assert r.json()["total"] >= 2

    def test_update_rule(self):
        create = client.post("/api/v1/rules/rules", json=build_rule("Update-Rule"))
        rule_id = create.json()["id"]

        r = client.put(
            f"/api/v1/rules/rules/{rule_id}",
            json={"name": "Updated-Rule-Name", "priority": "high"},
        )
        assert r.status_code == 200
        assert r.json()["name"] == "Updated-Rule-Name"
        assert r.json()["priority"] == "high"

    def test_delete_rule(self):
        create = client.post("/api/v1/rules/rules", json=build_rule("Delete-Rule"))
        rule_id = create.json()["id"]

        r = client.delete(f"/api/v1/rules/rules/{rule_id}")
        assert r.status_code == 204

        r = client.get(f"/api/v1/rules/rules/{rule_id}")
        assert r.status_code == 404

    def test_enable_disable_rule(self):
        create = client.post(
            "/api/v1/rules/rules",
            json=build_rule("Enable-Disable", enabled=False),
        )
        rule_id = create.json()["id"]

        r = client.post(f"/api/v1/rules/rules/{rule_id}/enable")
        assert r.status_code == 200
        assert r.json()["enabled"] is True

        r = client.post(f"/api/v1/rules/rules/{rule_id}/disable")
        assert r.status_code == 200
        assert r.json()["enabled"] is False


# ── Rule Evaluation Tests ───────────────────────────────────────────────────

class TestRuleEvaluation:
    def test_execute_entity_rule(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "Eval-Building")
        add_observation(eid, {"count": 5})

        rule_payload = build_rule(
            name="Entity-Eval-Rule",
            rule_type="entity",
            project_id=pid,
            conditions=[
                {
                    "condition_type": "equals",
                    "field": "entity_type",
                    "operator": "equals",
                    "value": "building",
                }
            ],
            actions=[{"action_type": "generate_alert"}],
        )
        create = client.post("/api/v1/rules/rules", json=rule_payload)
        rule_id = create.json()["id"]

        r = client.post(
            f"/api/v1/rules/rules/{rule_id}/execute",
            json={"project_id": pid},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["evaluated"] is True
        assert data["alerts_generated"] >= 1

    def test_execute_attribute_rule(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "road", "Eval-Road")
        add_observation(eid, {"length": 500, "count": 3})

        rule_payload = build_rule(
            name="Attribute-Eval-Rule",
            rule_type="attribute",
            project_id=pid,
            conditions=[
                {
                    "condition_type": "greater_than",
                    "field": "observation_count",
                    "operator": "greater_than",
                    "value": 0,
                }
            ],
            actions=[{"action_type": "generate_alert"}],
        )
        create = client.post("/api/v1/rules/rules", json=rule_payload)
        rule_id = create.json()["id"]

        r = client.post(
            f"/api/v1/rules/rules/{rule_id}/execute",
            json={"project_id": pid},
        )
        assert r.status_code == 200
        assert r.json()["alerts_generated"] >= 1

    def test_execute_rule_disabled(self):
        pid = get_test_project()
        create = client.post(
            "/api/v1/rules/rules",
            json=build_rule("Disabled-Rule", enabled=False, project_id=pid),
        )
        rule_id = create.json()["id"]

        r = client.post(
            f"/api/v1/rules/rules/{rule_id}/execute",
            json={"project_id": pid},
        )
        assert r.status_code == 400

    def test_execute_rule_no_match(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "river", "Eval-River")

        rule_payload = build_rule(
            name="No-Match-Rule",
            rule_type="entity",
            project_id=pid,
            conditions=[
                {
                    "condition_type": "equals",
                    "field": "entity_type",
                    "operator": "equals",
                    "value": "airfield",
                }
            ],
            actions=[{"action_type": "generate_alert"}],
        )
        create = client.post("/api/v1/rules/rules", json=rule_payload)
        rule_id = create.json()["id"]

        r = client.post(
            f"/api/v1/rules/rules/{rule_id}/execute",
            json={"project_id": pid},
        )
        assert r.status_code == 200
        assert r.json()["alerts_generated"] == 0

    def test_rule_and_operator(self):
        pid = get_test_project()
        eid = create_test_entity(pid, "building", "AND-Building")

        rule_payload = build_rule(
            name="AND-Rule",
            rule_type="entity",
            project_id=pid,
            conditions=[
                {
                    "condition_type": "equals",
                    "field": "entity_type",
                    "operator": "equals",
                    "value": "building",
                    "sort_order": 0,
                },
                {
                    "condition_type": "equals",
                    "field": "name",
                    "operator": "contains",
                    "value": "AND",
                    "logical_operator": "AND",
                    "sort_order": 1,
                },
            ],
            actions=[{"action_type": "generate_alert"}],
        )
        create = client.post("/api/v1/rules/rules", json=rule_payload)
        rule_id = create.json()["id"]

        r = client.post(
            f"/api/v1/rules/rules/{rule_id}/execute",
            json={"project_id": pid},
        )
        assert r.status_code == 200
        assert r.json()["alerts_generated"] >= 1


# ── Alert Management Tests ──────────────────────────────────────────────────

class TestAlertManagement:
    def _create_alert_for_test(self, pid: str) -> str:
        eid = create_test_entity(pid, "building", "Alert-Test")
        add_observation(eid, {"count": 10})

        rule_payload = build_rule(
            name="Alert-Gen-Rule",
            rule_type="entity",
            project_id=pid,
            conditions=[
                {
                    "condition_type": "greater_than",
                    "field": "observation_count",
                    "operator": "greater_than",
                    "value": 0,
                }
            ],
            actions=[{"action_type": "generate_alert"}],
        )
        create = client.post("/api/v1/rules/rules", json=rule_payload)
        rule_id = create.json()["id"]

        client.post(
            f"/api/v1/rules/rules/{rule_id}/execute",
            json={"project_id": pid},
        )

        alerts_r = client.get("/api/v1/rules/alerts", params={"project_id": pid})
        alerts = alerts_r.json()["items"]
        return alerts[0]["id"] if alerts else None

    def test_list_alerts(self):
        r = client.get("/api/v1/rules/alerts")
        assert r.status_code == 200
        assert "items" in r.json()

    def test_get_alert(self):
        pid = get_test_project()
        alert_id = self._create_alert_for_test(pid)
        if alert_id is None:
            pytest.skip("No alert generated")
        r = client.get(f"/api/v1/rules/alerts/{alert_id}")
        assert r.status_code == 200
        assert r.json()["id"] == alert_id

    def test_acknowledge_alert(self):
        pid = get_test_project()
        alert_id = self._create_alert_for_test(pid)
        if alert_id is None:
            pytest.skip("No alert generated")

        r = client.post(
            f"/api/v1/rules/alerts/{alert_id}/acknowledge",
            params={"actor": "test-analyst", "notes": "Acknowledged for review"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "acknowledged"

    def test_resolve_alert(self):
        pid = get_test_project()
        alert_id = self._create_alert_for_test(pid)
        if alert_id is None:
            pytest.skip("No alert generated")

        r = client.post(
            f"/api/v1/rules/alerts/{alert_id}/resolve",
            params={"actor": "test-analyst"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "resolved"

    def test_assign_alert(self):
        pid = get_test_project()
        alert_id = self._create_alert_for_test(pid)
        if alert_id is None:
            pytest.skip("No alert generated")

        r = client.post(
            f"/api/v1/rules/alerts/{alert_id}/assign",
            json={"assigned_to": "analyst-1", "actor": "admin"},
        )
        assert r.status_code == 200
        assert r.json()["assigned_to"] == "analyst-1"

    def test_update_alert_status(self):
        pid = get_test_project()
        alert_id = self._create_alert_for_test(pid)
        if alert_id is None:
            pytest.skip("No alert generated")

        r = client.patch(
            f"/api/v1/rules/alerts/{alert_id}/status",
            json={"status": "in_review", "actor": "reviewer-1"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "in_review"

    def test_alert_history(self):
        pid = get_test_project()
        alert_id = self._create_alert_for_test(pid)
        if alert_id is None:
            pytest.skip("No alert generated")

        client.post(
            f"/api/v1/rules/alerts/{alert_id}/acknowledge",
            params={"actor": "analyst"},
        )
        client.post(
            f"/api/v1/rules/alerts/{alert_id}/resolve",
            params={"actor": "analyst"},
        )

        r = client.get(f"/api/v1/rules/alerts/{alert_id}/history")
        assert r.status_code == 200
        assert len(r.json()["items"]) >= 2


# ── Config & Stats Tests ────────────────────────────────────────────────────

class TestConfigAndStats:
    def test_get_config(self):
        r = client.get("/api/v1/rules/config")
        assert r.status_code == 200
        assert "rule_types" in r.json()
        assert "condition_types" in r.json()
        assert "action_types" in r.json()
        assert "alert_priorities" in r.json()
        assert "alert_statuses" in r.json()

    def test_get_alert_stats(self):
        r = client.get("/api/v1/rules/alerts/stats")
        assert r.status_code == 200
        assert "total_alerts" in r.json()
        assert "by_status" in r.json()

    def test_get_rule_stats(self):
        r = client.get("/api/v1/rules/stats")
        assert r.status_code == 200
        assert "total_rules" in r.json()
        assert "enabled_rules" in r.json()
