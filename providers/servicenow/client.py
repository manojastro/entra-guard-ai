from __future__ import annotations

import base64
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

import httpx

from app.config import Settings
from app.database import Database, utc_now
from .models import ServiceNowError, ServiceNowIncidentPayload, ServiceNowRecord


class ServiceNowClient(ABC):
    @abstractmethod
    def create_incident(self, payload: ServiceNowIncidentPayload) -> ServiceNowRecord: ...

    @abstractmethod
    def get_incident(self, sys_id: str) -> ServiceNowRecord: ...

    @abstractmethod
    def update_incident(self, sys_id: str, updates: dict[str, Any]) -> ServiceNowRecord: ...

    @abstractmethod
    def add_comment(self, sys_id: str, comment: str) -> ServiceNowRecord: ...

    @abstractmethod
    def resolve_incident(self, sys_id: str, close_notes: str = "Resolved in EntraGuard AI") -> ServiceNowRecord: ...


def _record_from_api(result: dict[str, Any]) -> ServiceNowRecord:
    def display(value: Any) -> str:
        if isinstance(value, dict):
            return str(value.get("display_value") or value.get("value") or "")
        return str(value or "")

    return ServiceNowRecord(
        sys_id=display(result.get("sys_id")),
        number=display(result.get("number")),
        short_description=display(result.get("short_description")),
        description=display(result.get("description")),
        state=display(result.get("state")),
        category=display(result.get("category")),
        subcategory=display(result.get("subcategory")),
        assignment_group=display(result.get("assignment_group")),
        impact=display(result.get("impact")),
        urgency=display(result.get("urgency")),
        created_at=display(result.get("sys_created_on")),
        updated_at=display(result.get("sys_updated_on")),
    )


class MockServiceNowClient(ServiceNowClient):
    def __init__(self, database: Database):
        self.database = database

    def create_incident(self, payload: ServiceNowIncidentPayload) -> ServiceNowRecord:
        counter = self.database.next_counter("mock_incident", 10001)
        now = utc_now()
        record = ServiceNowRecord(
            sys_id=uuid.uuid4().hex,
            number=f"INC{counter:07d}",
            short_description=payload.short_description,
            description=payload.description,
            state=payload.state,
            category=payload.category,
            subcategory=payload.subcategory,
            assignment_group=payload.assignment_group,
            impact=payload.impact,
            urgency=payload.urgency,
            created_at=now,
            updated_at=now,
        )
        self.database.save_mock_record(record.to_dict())
        return record

    def get_incident(self, sys_id: str) -> ServiceNowRecord:
        record = self.database.get_mock_record(sys_id)
        if not record:
            raise ServiceNowError("ServiceNow incident was not found.", retryable=False, status_code=404)
        return ServiceNowRecord(**record)

    def update_incident(self, sys_id: str, updates: dict[str, Any]) -> ServiceNowRecord:
        record = self.get_incident(sys_id)
        for key in ("short_description", "description", "state", "assignment_group"):
            if key in updates and updates[key] is not None:
                setattr(record, key, str(updates[key]))
        record.updated_at = utc_now()
        self.database.save_mock_record(record.to_dict())
        return record

    def add_comment(self, sys_id: str, comment: str) -> ServiceNowRecord:
        record = self.get_incident(sys_id)
        record.comments.append({"timestamp": utc_now(), "comment": comment})
        record.updated_at = utc_now()
        self.database.save_mock_record(record.to_dict())
        return record

    def resolve_incident(self, sys_id: str, close_notes: str = "Resolved in EntraGuard AI") -> ServiceNowRecord:
        record = self.add_comment(sys_id, close_notes)
        return self.update_incident(record.sys_id, {"state": "6"})


class LiveServiceNowClient(ServiceNowClient):
    fields = (
        "sys_id,number,short_description,description,state,category,subcategory,"
        "assignment_group,impact,urgency,sys_created_on,sys_updated_on"
    )

    def __init__(self, settings: Settings):
        if not settings.servicenow_instance_url:
            raise ServiceNowError("ServiceNow instance URL is not configured.", retryable=False)
        self.settings = settings
        self.base_url = f"{settings.servicenow_instance_url}/api/now/table/incident"
        self.http = httpx.Client(timeout=20.0)
        self._token: str | None = None

    def _auth_headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.settings.servicenow_client_id and self.settings.servicenow_client_secret:
            if not self._token:
                try:
                    response = self.http.post(
                        f"{self.settings.servicenow_instance_url}/oauth_token.do",
                        data={
                            "grant_type": "client_credentials",
                            "client_id": self.settings.servicenow_client_id,
                            "client_secret": self.settings.servicenow_client_secret,
                        },
                    )
                    response.raise_for_status()
                    self._token = response.json()["access_token"]
                except (httpx.HTTPError, KeyError, ValueError) as exc:
                    raise ServiceNowError("ServiceNow OAuth authentication failed.") from exc
            headers["Authorization"] = f"Bearer {self._token}"
        elif self.settings.servicenow_username and self.settings.servicenow_password:
            value = base64.b64encode(
                f"{self.settings.servicenow_username}:{self.settings.servicenow_password}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {value}"
        else:
            raise ServiceNowError("ServiceNow authentication is not configured.", retryable=False)
        return headers

    def _request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = self.http.request(method, url, headers=self._auth_headers(), **kwargs)
            if response.status_code == 401 and self._token:
                self._token = None
                response = self.http.request(method, url, headers=self._auth_headers(), **kwargs)
            response.raise_for_status()
            result = response.json().get("result")
            if not isinstance(result, dict):
                raise ServiceNowError("ServiceNow returned an unexpected response.")
            return result
        except ServiceNowError:
            raise
        except httpx.TimeoutException as exc:
            raise ServiceNowError("ServiceNow request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            retryable = status >= 500 or status == 429
            # Do not include response bodies; they may contain instance details.
            raise ServiceNowError(
                f"ServiceNow request failed with HTTP {status}.", retryable=retryable, status_code=status
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise ServiceNowError("ServiceNow is currently unavailable.") from exc

    def create_incident(self, payload: ServiceNowIncidentPayload) -> ServiceNowRecord:
        result = self._request(
            "POST", self.base_url, params={"sysparm_fields": self.fields}, json=payload.to_api_dict()
        )
        return _record_from_api(result)

    def get_incident(self, sys_id: str) -> ServiceNowRecord:
        result = self._request(
            "GET", f"{self.base_url}/{sys_id}", params={"sysparm_display_value": "true", "sysparm_fields": self.fields}
        )
        return _record_from_api(result)

    def update_incident(self, sys_id: str, updates: dict[str, Any]) -> ServiceNowRecord:
        result = self._request(
            "PATCH", f"{self.base_url}/{sys_id}", params={"sysparm_fields": self.fields}, json=updates
        )
        return _record_from_api(result)

    def add_comment(self, sys_id: str, comment: str) -> ServiceNowRecord:
        return self.update_incident(sys_id, {"work_notes": comment})

    def resolve_incident(self, sys_id: str, close_notes: str = "Resolved in EntraGuard AI") -> ServiceNowRecord:
        return self.update_incident(
            sys_id,
            {"state": "6", "close_code": "Solved (Permanently)", "close_notes": close_notes},
        )


def create_client(settings: Settings, database: Database) -> ServiceNowClient:
    if settings.servicenow_mode == "mock":
        return MockServiceNowClient(database)
    return LiveServiceNowClient(settings)

