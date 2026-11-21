from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.database import Database
from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    database = Database(str(tmp_path / "test.db"))
    settings = Settings(
        database_path=str(tmp_path / "test.db"),
        servicenow_enabled=True,
        servicenow_mode="mock",
        servicenow_assignment_group="Identity Security Team",
        servicenow_assignment_groups=["Identity Security Team", "SOC"],
    )
    return TestClient(create_app(settings=settings, database=database))


def test_demo_incident_and_verified_preview(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/incidents/EG-2026-0045")
        assert response.status_code == 200
        incident = response.json()
        assert incident["risk_score"] == 96
        assert incident["severity"] == "Critical"
        assert incident["service_now_sys_id"] is None

        preview = client.get("/api/incidents/EG-2026-0045/servicenow/preview").json()
        assert preview["short_description"] == "[EntraGuard AI] Critical - Possible Privileged Account Takeover"
        assert "Global Administrator role activated" in preview["description"]
        assert "Verified Evidence" in preview["description"]
        assert preview["impact"] == "1"
        assert preview["urgency"] == "1"


def test_create_is_duplicate_safe_and_persists_link(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        created = client.post(
            "/api/incidents/EG-2026-0045/servicenow",
            json={"assignment_group": "SOC"},
            headers={"X-Analyst": "Test Analyst"},
        )
        assert created.status_code == 200
        body = created.json()
        assert body["service_now"]["number"] == "INC0010001"
        assert body["service_now"]["assignment_group"] == "SOC"
        assert body["service_now"]["status"] == "In Progress"
        assert body.get("duplicate_prevented") is None

        duplicate = client.post("/api/incidents/EG-2026-0045/servicenow", json={})
        assert duplicate.status_code == 200
        assert duplicate.json()["duplicate_prevented"] is True
        assert duplicate.json()["service_now"]["number"] == "INC0010001"

        incidents = client.get("/api/incidents").json()["items"]
        assert sum(1 for item in incidents if item["service_now_incident_number"] == "INC0010001") == 1


def test_comment_status_sync_and_audit(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        client.post("/api/incidents/EG-2026-0045/servicenow", json={})

        comment = client.post(
            "/api/incidents/EG-2026-0045/servicenow/comment",
            json={"comment": "User denied the privileged role activation. Sessions revoked."},
        )
        assert comment.status_code == 200
        assert comment.json()["comment_added"] is True

        status = client.patch(
            "/api/incidents/EG-2026-0045/status", json={"status": "Investigating"}
        )
        assert status.status_code == 200
        assert status.json()["service_now"]["status"] == "In Progress"

        audit = client.get("/api/incidents/EG-2026-0045/audit").json()["items"]
        actions = {event["action"] for event in audit}
        assert "ticket_created" in actions
        assert "comment_added" in actions
        assert "ticket_updated" in actions
        assert all(event["actor"] for event in audit)

        resolved = client.patch(
            "/api/incidents/EG-2026-0045/status", json={"status": "Resolved"}
        )
        assert resolved.status_code == 200
        assert resolved.json()["service_now"]["status"] == "Resolved"
        actions = {event["action"] for event in client.get("/api/incidents/EG-2026-0045/audit").json()["items"]}
        assert "ticket_resolved" in actions


def test_mock_service_now_page_and_demo_reset(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        created = client.post("/api/incidents/EG-2026-0045/servicenow", json={}).json()
        page = client.get(created["service_now"]["url"])
        assert page.status_code == 200
        assert "MOCK INSTANCE" in page.text
        assert "INC0010001" in page.text

        reset = client.post("/api/demo/reset")
        assert reset.status_code == 200
        incident = client.get("/api/incidents/EG-2026-0045").json()
        assert incident["service_now_incident_number"] is None


def test_disabled_integration_does_not_create(tmp_path: Path) -> None:
    database = Database(str(tmp_path / "disabled.db"))
    settings = Settings(
        database_path=str(tmp_path / "disabled.db"),
        servicenow_enabled=False,
        servicenow_mode="mock",
    )
    with TestClient(create_app(settings=settings, database=database)) as client:
        response = client.post("/api/incidents/EG-2026-0045/servicenow", json={})
        assert response.status_code == 400
        assert response.json()["detail"] == "ServiceNow integration is disabled."
