from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class Database:
    def __init__(self, path: str):
        self.path = path
        self._write_lock = threading.RLock()
        if path != ":memory:":
            Path(path).resolve().parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def init(self) -> None:
        with self._write_lock, self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS security_incidents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    risk_score INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    identity_name TEXT NOT NULL,
                    identity_email TEXT NOT NULL,
                    detected_at TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    country TEXT NOT NULL,
                    device TEXT NOT NULL,
                    application TEXT NOT NULL,
                    privileged INTEGER NOT NULL DEFAULT 0,
                    detection_reason TEXT NOT NULL,
                    ai_summary TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    timeline_json TEXT NOT NULL,
                    investigation_json TEXT NOT NULL,
                    remediation_json TEXT NOT NULL,
                    service_now_incident_id TEXT,
                    service_now_incident_number TEXT,
                    service_now_sys_id TEXT,
                    service_now_status TEXT,
                    service_now_url TEXT,
                    service_now_created_at TEXT,
                    service_now_updated_at TEXT,
                    service_now_assignment_group TEXT,
                    service_now_last_sync_at TEXT,
                    service_now_retry_count INTEGER NOT NULL DEFAULT 0,
                    service_now_last_error TEXT,
                    service_now_last_retry_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY,
                    actor TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    incident_id TEXT NOT NULL,
                    service_now_incident_number TEXT,
                    action TEXT NOT NULL,
                    result TEXT NOT NULL,
                    detail TEXT,
                    FOREIGN KEY (incident_id) REFERENCES security_incidents(id)
                );

                CREATE TABLE IF NOT EXISTS mock_servicenow_records (
                    sys_id TEXT PRIMARY KEY,
                    number TEXT UNIQUE NOT NULL,
                    short_description TEXT NOT NULL,
                    description TEXT NOT NULL,
                    state TEXT NOT NULL,
                    category TEXT,
                    subcategory TEXT,
                    assignment_group TEXT,
                    impact TEXT,
                    urgency TEXT,
                    comments_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS counters (
                    name TEXT PRIMARY KEY,
                    value INTEGER NOT NULL
                );
                """
            )

    @staticmethod
    def _incident_from_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        item = dict(row)
        for key in ("evidence_json", "timeline_json", "investigation_json", "remediation_json"):
            output_key = key.removesuffix("_json")
            item[output_key] = json.loads(item.pop(key))
        item["privileged"] = bool(item["privileged"])
        return item

    def list_incidents(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM security_incidents ORDER BY risk_score DESC, detected_at DESC"
            ).fetchall()
        return [self._incident_from_row(row) for row in rows if row is not None]

    def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM security_incidents WHERE id = ?", (incident_id,)).fetchone()
        return self._incident_from_row(row)

    def update_incident(self, incident_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        if not updates:
            return self.get_incident(incident_id)
        allowed = {
            "status", "service_now_incident_id", "service_now_incident_number", "service_now_sys_id",
            "service_now_status", "service_now_url", "service_now_created_at", "service_now_updated_at",
            "service_now_assignment_group", "service_now_last_sync_at", "service_now_retry_count",
            "service_now_last_error", "service_now_last_retry_at", "updated_at",
        }
        safe_updates = {key: value for key, value in updates.items() if key in allowed}
        safe_updates["updated_at"] = utc_now()
        columns = ", ".join(f"{key} = ?" for key in safe_updates)
        values = [*safe_updates.values(), incident_id]
        with self._write_lock, self.connect() as connection:
            connection.execute(f"UPDATE security_incidents SET {columns} WHERE id = ?", values)
        return self.get_incident(incident_id)

    def insert_incident(self, incident: dict[str, Any]) -> None:
        payload = dict(incident)
        for key in ("evidence", "timeline", "investigation", "remediation"):
            payload[f"{key}_json"] = json.dumps(payload.pop(key))
        payload["privileged"] = int(payload["privileged"])
        columns = ", ".join(payload)
        placeholders = ", ".join("?" for _ in payload)
        with self._write_lock, self.connect() as connection:
            connection.execute(
                f"INSERT OR IGNORE INTO security_incidents ({columns}) VALUES ({placeholders})",
                list(payload.values()),
            )

    def add_audit(
        self,
        actor: str,
        incident_id: str,
        action: str,
        result: str,
        service_now_number: str | None = None,
        detail: str | None = None,
    ) -> dict[str, Any]:
        event = {
            "id": str(uuid.uuid4()),
            "actor": actor,
            "timestamp": utc_now(),
            "incident_id": incident_id,
            "service_now_incident_number": service_now_number,
            "action": action,
            "result": result,
            "detail": detail,
        }
        with self._write_lock, self.connect() as connection:
            connection.execute(
                """INSERT INTO audit_events
                (id, actor, timestamp, incident_id, service_now_incident_number, action, result, detail)
                VALUES (:id, :actor, :timestamp, :incident_id, :service_now_incident_number, :action, :result, :detail)""",
                event,
            )
        return event

    def list_audit(self, incident_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as connection:
            if incident_id:
                rows = connection.execute(
                    "SELECT * FROM audit_events WHERE incident_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (incident_id, limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM audit_events ORDER BY timestamp DESC LIMIT ?", (limit,)
                ).fetchall()
        return [dict(row) for row in rows]

    def next_counter(self, name: str, start: int) -> int:
        with self._write_lock, self.connect() as connection:
            row = connection.execute("SELECT value FROM counters WHERE name = ?", (name,)).fetchone()
            value = (row["value"] + 1) if row else start
            connection.execute(
                "INSERT INTO counters(name, value) VALUES(?, ?) ON CONFLICT(name) DO UPDATE SET value=excluded.value",
                (name, value),
            )
        return value

    def save_mock_record(self, record: dict[str, Any]) -> None:
        payload = dict(record)
        payload["comments_json"] = json.dumps(payload.pop("comments", []))
        with self._write_lock, self.connect() as connection:
            connection.execute(
                """INSERT INTO mock_servicenow_records
                (sys_id, number, short_description, description, state, category, subcategory,
                 assignment_group, impact, urgency, comments_json, created_at, updated_at)
                VALUES (:sys_id, :number, :short_description, :description, :state, :category, :subcategory,
                 :assignment_group, :impact, :urgency, :comments_json, :created_at, :updated_at)
                ON CONFLICT(sys_id) DO UPDATE SET
                 short_description=excluded.short_description, description=excluded.description,
                 state=excluded.state, assignment_group=excluded.assignment_group,
                 comments_json=excluded.comments_json, updated_at=excluded.updated_at""",
                payload,
            )

    def get_mock_record(self, sys_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM mock_servicenow_records WHERE sys_id = ?", (sys_id,)
            ).fetchone()
        if not row:
            return None
        record = dict(row)
        record["comments"] = json.loads(record.pop("comments_json"))
        return record

    def clear_demo_data(self) -> None:
        with self._write_lock, self.connect() as connection:
            connection.execute("DELETE FROM audit_events")
            connection.execute("DELETE FROM mock_servicenow_records")
            connection.execute("DELETE FROM security_incidents")
            connection.execute("DELETE FROM counters WHERE name = 'mock_incident'")


def seed_demo_data(database: Database) -> None:
    now = utc_now()
    incidents = [
        {
            "id": "EG-2026-0045",
            "title": "Possible Privileged Account Takeover",
            "severity": "Critical",
            "risk_score": 96,
            "status": "Open",
            "identity_name": "John Doe",
            "identity_email": "john.doe@company.com",
            "detected_at": "2026-08-23T02:24:00+00:00",
            "ip_address": "185.220.101.42",
            "country": "Romania",
            "device": "Unknown Linux device",
            "application": "Microsoft Azure Management",
            "privileged": True,
            "detection_reason": "A foreign sign-in was followed by an MFA method change, privileged role activation, and application consent within 10 minutes.",
            "ai_summary": "The activity is highly abnormal compared with the identity's established behavior. The sequence of authentication changes and privileged actions is consistent with a possible privileged account takeover. All assertions are grounded in the correlated events below.",
            "evidence": [
                {"label": "Unfamiliar source", "value": "185.220.101.42 · Romania", "verified": True},
                {"label": "Privilege", "value": "Global Administrator activated", "verified": True},
                {"label": "Persistence", "value": "New MFA method registered", "verified": True},
                {"label": "Cloud action", "value": "Admin consent granted", "verified": True},
            ],
            "timeline": [
                {"time": "02:14", "event": "Successful login from new country", "source": "Entra sign-in logs"},
                {"time": "02:16", "event": "MFA authentication method added", "source": "Entra audit logs"},
                {"time": "02:19", "event": "Global Administrator role activated", "source": "Privileged Identity Management"},
                {"time": "02:22", "event": "New application registered", "source": "Entra audit logs"},
                {"time": "02:24", "event": "Admin consent granted", "source": "Entra audit logs"},
            ],
            "investigation": ["Verify the activity with the user using a trusted channel.", "Review the source IP and correlated sign-in activity.", "Validate the MFA registration and PIM activation.", "Review the new application's permissions and consent grants."],
            "remediation": ["Revoke active sessions.", "Reset the identity's password.", "Remove any unauthorized MFA method and privilege.", "Quarantine and investigate the newly created application."],
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "EG-2026-0044",
            "title": "Impossible Travel Sign-in Sequence",
            "severity": "High",
            "risk_score": 82,
            "status": "Investigating",
            "identity_name": "Aisha Khan",
            "identity_email": "aisha.khan@company.com",
            "detected_at": "2026-08-23T01:48:00+00:00",
            "ip_address": "103.28.54.16",
            "country": "Singapore",
            "device": "Windows 11 · Managed",
            "application": "Microsoft 365",
            "privileged": False,
            "detection_reason": "Successful sign-ins originated from two geographically distant locations within 32 minutes.",
            "ai_summary": "The travel velocity is not physically possible. The managed device signal lowers confidence in compromise, but token replay or VPN egress should be investigated.",
            "evidence": [{"label": "Travel velocity", "value": "14,200 km in 32 minutes", "verified": True}, {"label": "Device trust", "value": "Managed and compliant", "verified": True}],
            "timeline": [{"time": "01:16", "event": "Successful sign-in from London", "source": "Entra sign-in logs"}, {"time": "01:48", "event": "Successful sign-in from Singapore", "source": "Entra sign-in logs"}],
            "investigation": ["Confirm the user's current location.", "Review token and device identifiers."],
            "remediation": ["Revoke sessions if activity is unrecognized.", "Require phishing-resistant MFA."],
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "EG-2026-0043",
            "title": "Legacy Authentication Attempt",
            "severity": "Medium",
            "risk_score": 61,
            "status": "Open",
            "identity_name": "Marco Silva",
            "identity_email": "marco.silva@company.com",
            "detected_at": "2026-08-22T23:12:00+00:00",
            "ip_address": "172.58.44.91",
            "country": "United States",
            "device": "Unknown",
            "application": "Exchange Online",
            "privileged": False,
            "detection_reason": "A legacy IMAP client attempted authentication from an unmanaged source.",
            "ai_summary": "The attempt was blocked by Conditional Access. No successful session or subsequent activity was observed.",
            "evidence": [{"label": "Control result", "value": "Blocked by Conditional Access", "verified": True}],
            "timeline": [{"time": "23:12", "event": "Legacy IMAP authentication blocked", "source": "Entra sign-in logs"}],
            "investigation": ["Confirm whether a legacy mail client is expected."],
            "remediation": ["Keep legacy authentication blocked."],
            "created_at": now,
            "updated_at": now,
        },
    ]
    for incident in incidents:
        database.insert_incident(incident)
