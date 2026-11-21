from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ServiceNowIncidentPayload:
    short_description: str
    description: str
    category: str
    subcategory: str
    assignment_group: str
    impact: str
    urgency: str
    correlation_id: str
    state: str = "1"

    def to_api_dict(self) -> dict[str, str]:
        # ServiceNow calculates priority from impact and urgency. We intentionally
        # avoid writing the calculated priority field directly.
        return {
            "short_description": self.short_description,
            "description": self.description,
            "category": self.category,
            "subcategory": self.subcategory,
            "assignment_group": self.assignment_group,
            "impact": self.impact,
            "urgency": self.urgency,
            "correlation_id": self.correlation_id,
            "state": self.state,
        }


@dataclass(slots=True)
class ServiceNowRecord:
    sys_id: str
    number: str
    short_description: str
    description: str
    state: str
    category: str = ""
    subcategory: str = ""
    assignment_group: str = ""
    impact: str = ""
    urgency: str = ""
    comments: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ServiceNowError(RuntimeError):
    def __init__(self, message: str, *, retryable: bool = True, status_code: int | None = None):
        super().__init__(message)
        self.retryable = retryable
        self.status_code = status_code

