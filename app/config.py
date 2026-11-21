from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


DEFAULT_PRIORITY_MAP = {
    "Critical": {"impact": "1", "urgency": "1"},
    "High": {"impact": "1", "urgency": "2"},
    "Medium": {"impact": "2", "urgency": "2"},
    "Low": {"impact": "2", "urgency": "3"},
    "Informational": {"impact": "3", "urgency": "3"},
}


@dataclass(slots=True)
class Settings:
    app_env: str = "development"
    database_path: str = "entraguard.db"
    servicenow_enabled: bool = True
    servicenow_mode: str = "mock"
    servicenow_auto_create: bool = False
    servicenow_auto_create_min_severity: str = "Critical"
    servicenow_instance_url: str = ""
    servicenow_username: str = ""
    servicenow_password: str = ""
    servicenow_client_id: str = ""
    servicenow_client_secret: str = ""
    servicenow_assignment_group: str = "Identity Security Team"
    servicenow_assignment_groups: list[str] = field(default_factory=list)
    servicenow_default_category: str = "Security"
    servicenow_default_subcategory: str = "Identity Security"
    servicenow_priority_map: dict[str, dict[str, str]] = field(default_factory=lambda: DEFAULT_PRIORITY_MAP.copy())
    servicenow_max_retries: int = 2
    servicenow_rate_limit_per_minute: int = 10

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv(Path(".env"))
        try:
            priority_map = json.loads(os.getenv("SERVICENOW_PRIORITY_MAP", json.dumps(DEFAULT_PRIORITY_MAP)))
        except json.JSONDecodeError:
            priority_map = DEFAULT_PRIORITY_MAP.copy()
        default_group = os.getenv("SERVICENOW_ASSIGNMENT_GROUP", "Identity Security Team")
        groups = [
            item.strip()
            for item in os.getenv(
                "SERVICENOW_ASSIGNMENT_GROUPS",
                "Identity Security Team,SOC,IAM Operations,Cybersecurity Operations,Security Incident Response",
            ).split(",")
            if item.strip()
        ]
        if default_group and default_group not in groups:
            groups.insert(0, default_group)
        return cls(
            app_env=os.getenv("APP_ENV", "development"),
            database_path=os.getenv("DATABASE_PATH", "entraguard.db"),
            servicenow_enabled=_bool("SERVICENOW_ENABLED", True),
            servicenow_mode=os.getenv("SERVICENOW_MODE", "mock").lower(),
            servicenow_auto_create=_bool("SERVICENOW_AUTO_CREATE", False),
            servicenow_auto_create_min_severity=os.getenv("SERVICENOW_AUTO_CREATE_MIN_SEVERITY", "Critical"),
            servicenow_instance_url=os.getenv("SERVICENOW_INSTANCE_URL", "").rstrip("/"),
            servicenow_username=os.getenv("SERVICENOW_USERNAME", ""),
            servicenow_password=os.getenv("SERVICENOW_PASSWORD", ""),
            servicenow_client_id=os.getenv("SERVICENOW_CLIENT_ID", ""),
            servicenow_client_secret=os.getenv("SERVICENOW_CLIENT_SECRET", ""),
            servicenow_assignment_group=default_group,
            servicenow_assignment_groups=groups,
            servicenow_default_category=os.getenv("SERVICENOW_DEFAULT_CATEGORY", "Security"),
            servicenow_default_subcategory=os.getenv("SERVICENOW_DEFAULT_SUBCATEGORY", "Identity Security"),
            servicenow_priority_map=priority_map,
            servicenow_max_retries=max(0, int(os.getenv("SERVICENOW_MAX_RETRIES", "2"))),
            servicenow_rate_limit_per_minute=max(1, int(os.getenv("SERVICENOW_RATE_LIMIT_PER_MINUTE", "10"))),
        )

