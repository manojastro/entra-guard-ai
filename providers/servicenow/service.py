from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any, Callable

from app.config import Settings
from app.database import Database, utc_now
from .client import ServiceNowClient, create_client
from .mapper import ENTRAGUARD_TO_SERVICENOW_STATE, build_payload, state_name, ticket_preview
from .models import ServiceNowError, ServiceNowRecord


class ServiceNowIntegrationService:
    def __init__(self, settings: Settings, database: Database):
        self.settings = settings
        self.database = database
        self.client: ServiceNowClient | None = None
        self._create_lock = threading.RLock()
        self._create_times: deque[float] = deque()

    def _client(self) -> ServiceNowClient:
        if self.client is None:
            self.client = create_client(self.settings, self.database)
        return self.client

    def _require_enabled(self) -> None:
        if not self.settings.servicenow_enabled:
            raise ServiceNowError("ServiceNow integration is disabled.", retryable=False)

    def _incident(self, incident_id: str) -> dict[str, Any]:
        incident = self.database.get_incident(incident_id)
        if not incident:
            raise KeyError(incident_id)
        return incident

    def _check_rate_limit(self) -> None:
        now = time.monotonic()
        while self._create_times and now - self._create_times[0] > 60:
            self._create_times.popleft()
        if len(self._create_times) >= self.settings.servicenow_rate_limit_per_minute:
            raise ServiceNowError("ServiceNow ticket creation rate limit reached. Please retry shortly.")
        self._create_times.append(now)

    def _with_retries(self, operation: Callable[[], ServiceNowRecord]) -> tuple[ServiceNowRecord, int]:
        attempts = 0
        while True:
            try:
                return operation(), attempts
            except ServiceNowError as exc:
                if not exc.retryable or attempts >= self.settings.servicenow_max_retries:
                    raise
                attempts += 1
                time.sleep(min(0.2 * (2 ** (attempts - 1)), 1.0))

    def preview(self, incident_id: str) -> dict[str, Any]:
        return ticket_preview(self._incident(incident_id), self.settings)

    def create_incident(
        self,
        incident_id: str,
        *,
        actor: str,
        assignment_group: str | None = None,
        short_description: str | None = None,
        description: str | None = None,
        automatic: bool = False,
    ) -> dict[str, Any]:
        self._require_enabled()
        with self._create_lock:
            incident = self._incident(incident_id)
            if incident.get("service_now_sys_id"):
                self.database.add_audit(
                    actor, incident_id, "ticket_create_duplicate_prevented", "skipped",
                    incident.get("service_now_incident_number"), "Existing linked ServiceNow incident returned."
                )
                return self._response(incident, duplicate_prevented=True)
            self._check_rate_limit()
            payload = build_payload(
                incident,
                self.settings,
                assignment_group=assignment_group,
                short_description=short_description,
                description=description,
            )
            # Raising a critical ticket is the analyst's explicit acceptance of
            # triage ownership, so the demo workflow begins in progress.
            begins_investigation = incident["severity"] == "Critical" and incident["status"] == "Open"
            if begins_investigation:
                payload.state = "2"
            try:
                record, retry_count = self._with_retries(lambda: self._client().create_incident(payload))
            except ServiceNowError as exc:
                failed = self.database.update_incident(
                    incident_id,
                    {
                        "service_now_retry_count": incident.get("service_now_retry_count", 0) + 1,
                        "service_now_last_error": str(exc),
                        "service_now_last_retry_at": utc_now(),
                    },
                )
                self.database.add_audit(
                    actor, incident_id, "ticket_creation_failed", "failed", None, str(exc)
                )
                raise
            now = utc_now()
            url = (
                f"{self.settings.servicenow_instance_url}/nav_to.do?uri=incident.do?sys_id={record.sys_id}"
                if self.settings.servicenow_mode != "mock"
                else f"/mock-servicenow/incidents/{record.sys_id}"
            )
            incident = self.database.update_incident(
                incident_id,
                {
                    "service_now_incident_id": record.sys_id,
                    "service_now_incident_number": record.number,
                    "service_now_sys_id": record.sys_id,
                    "service_now_status": state_name(record.state),
                    "service_now_url": url,
                    "service_now_created_at": record.created_at or now,
                    "service_now_updated_at": record.updated_at or now,
                    "service_now_assignment_group": record.assignment_group,
                    "service_now_last_sync_at": now,
                    "service_now_retry_count": retry_count,
                    "service_now_last_error": None,
                    "service_now_last_retry_at": now if retry_count else None,
                    **({"status": "Investigating"} if begins_investigation else {}),
                },
            )
            self.database.add_audit(
                actor,
                incident_id,
                "ticket_created_automatically" if automatic else "ticket_created",
                "success",
                record.number,
                f"Assigned to {record.assignment_group or 'unassigned'}",
            )
            return self._response(incident)

    def get_incident(self, incident_id: str, *, actor: str, synchronize: bool = True) -> dict[str, Any]:
        self._require_enabled()
        incident = self._incident(incident_id)
        if not incident.get("service_now_sys_id"):
            raise LookupError("No ServiceNow incident is linked.")
        if synchronize:
            try:
                record, _ = self._with_retries(
                    lambda: self._client().get_incident(incident["service_now_sys_id"])
                )
                incident = self._persist_record(incident_id, record)
                self.database.add_audit(
                    actor, incident_id, "synchronization_attempted", "success", record.number,
                    f"ServiceNow status: {state_name(record.state)}"
                )
            except ServiceNowError as exc:
                self.database.add_audit(
                    actor, incident_id, "synchronization_failed", "failed",
                    incident.get("service_now_incident_number"), str(exc)
                )
        return self._response(incident)

    def update_incident(self, incident_id: str, updates: dict[str, Any], *, actor: str) -> dict[str, Any]:
        self._require_enabled()
        incident = self._incident(incident_id)
        if not incident.get("service_now_sys_id"):
            raise LookupError("No ServiceNow incident is linked.")
        api_updates: dict[str, Any] = {}
        if updates.get("status"):
            requested = updates["status"]
            api_updates["state"] = ENTRAGUARD_TO_SERVICENOW_STATE.get(requested, requested)
        if updates.get("assignment_group"):
            api_updates["assignment_group"] = updates["assignment_group"]
        if updates.get("short_description"):
            api_updates["short_description"] = updates["short_description"]
        is_resolution = updates.get("status") == "Resolved"
        try:
            if is_resolution:
                record, _ = self._with_retries(
                    lambda: self._client().resolve_incident(
                        incident["service_now_sys_id"], "Resolved by EntraGuard analyst workflow."
                    )
                )
                remaining = {key: value for key, value in api_updates.items() if key != "state"}
                if remaining:
                    record, _ = self._with_retries(
                        lambda: self._client().update_incident(incident["service_now_sys_id"], remaining)
                    )
            else:
                record, _ = self._with_retries(
                    lambda: self._client().update_incident(incident["service_now_sys_id"], api_updates)
                )
        except ServiceNowError as exc:
            self.database.add_audit(
                actor, incident_id, "ticket_resolution_failed" if is_resolution else "ticket_update_failed",
                "failed", incident.get("service_now_incident_number"), str(exc)
            )
            raise
        incident = self._persist_record(incident_id, record)
        self.database.add_audit(
            actor, incident_id, "ticket_resolved" if is_resolution else "ticket_updated", "success", record.number,
            ", ".join(api_updates) or "No fields changed"
        )
        return self._response(incident)

    def add_comment(self, incident_id: str, comment: str, *, actor: str) -> dict[str, Any]:
        self._require_enabled()
        incident = self._incident(incident_id)
        if not incident.get("service_now_sys_id"):
            raise LookupError("No ServiceNow incident is linked.")
        try:
            record, _ = self._with_retries(
                lambda: self._client().add_comment(incident["service_now_sys_id"], comment)
            )
        except ServiceNowError as exc:
            self.database.add_audit(
                actor, incident_id, "comment_add_failed", "failed",
                incident.get("service_now_incident_number"), str(exc)
            )
            raise
        incident = self._persist_record(incident_id, record)
        self.database.add_audit(
            actor, incident_id, "comment_added", "success", record.number,
            f"Investigation update sent ({len(comment)} characters)."
        )
        return self._response(incident, comment_added=True)

    def sync_entraguard_status(self, incident_id: str, status: str, *, actor: str) -> dict[str, Any]:
        incident = self.database.update_incident(incident_id, {"status": status})
        if not incident:
            raise KeyError(incident_id)
        self.database.add_audit(actor, incident_id, "entraguard_status_updated", "success", incident.get("service_now_incident_number"), status)
        if incident.get("service_now_sys_id") and self.settings.servicenow_enabled:
            # One-way, action-triggered synchronization avoids polling loops.
            try:
                return self.update_incident(incident_id, {"status": status}, actor=actor)
            except ServiceNowError as exc:
                self.database.add_audit(
                    actor, incident_id, "synchronization_failed", "failed",
                    incident.get("service_now_incident_number"), str(exc)
                )
                raise
        return {"incident": incident, "service_now": None}

    def _persist_record(self, incident_id: str, record: ServiceNowRecord) -> dict[str, Any]:
        return self.database.update_incident(
            incident_id,
            {
                "service_now_incident_number": record.number,
                "service_now_status": state_name(record.state),
                "service_now_updated_at": record.updated_at or utc_now(),
                "service_now_assignment_group": record.assignment_group,
                "service_now_last_sync_at": utc_now(),
                "service_now_last_error": None,
            },
        ) or self._incident(incident_id)

    @staticmethod
    def _response(incident: dict[str, Any], **extra: Any) -> dict[str, Any]:
        response = {
            "incident_id": incident["id"],
            "service_now": {
                "incident_id": incident.get("service_now_incident_id"),
                "number": incident.get("service_now_incident_number"),
                "sys_id": incident.get("service_now_sys_id"),
                "status": incident.get("service_now_status"),
                "url": incident.get("service_now_url"),
                "created_at": incident.get("service_now_created_at"),
                "updated_at": incident.get("service_now_updated_at"),
                "assignment_group": incident.get("service_now_assignment_group"),
                "last_sync_at": incident.get("service_now_last_sync_at"),
            },
        }
        response.update(extra)
        return response
