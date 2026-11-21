from __future__ import annotations

from typing import Any

from app.config import Settings
from .models import ServiceNowIncidentPayload


SERVICENOW_STATE_NAMES = {
    "1": "New",
    "2": "In Progress",
    "3": "On Hold",
    "6": "Resolved",
    "7": "Closed",
    "8": "Canceled",
}

ENTRAGUARD_TO_SERVICENOW_STATE = {
    "Open": "1",
    "Investigating": "2",
    "Resolved": "6",
    "Closed": "7",
}


def state_name(state: str | int | None) -> str:
    value = str(state or "1")
    return SERVICENOW_STATE_NAMES.get(value, value)


def format_ticket_description(incident: dict[str, Any]) -> str:
    timeline = "\n".join(
        f"{event['time']} - {event['event']} (Source: {event['source']})"
        for event in incident["timeline"]
    )
    evidence = "\n".join(
        f"- {item['label']}: {item['value']}" for item in incident["evidence"] if item.get("verified")
    )
    investigation = "\n".join(
        f"{index}. {item}" for index, item in enumerate(incident["investigation"], start=1)
    )
    remediation = "\n".join(
        f"{index}. {item}" for index, item in enumerate(incident["remediation"], start=1)
    )
    return f"""EntraGuard AI Security Incident

Incident:
{incident['id']}

Affected Identity:
{incident['identity_name']} <{incident['identity_email']}>

Severity:
{incident['severity']}

Risk Score:
{incident['risk_score']}/100

Detection Time:
{incident['detected_at']}

Source:
IP: {incident['ip_address']}
Country: {incident['country']}
Device: {incident['device']}
Application: {incident['application']}
Privileged Identity: {'Yes' if incident['privileged'] else 'No'}

Detection:
{incident['title']}

Detection Reason:
{incident['detection_reason']}

Timeline:
{timeline}

Verified Evidence:
{evidence}

AI Assessment:
{incident['ai_summary']}

Recommended Investigation:
{investigation}

Recommended Remediation:
{remediation}
""".strip()


def build_payload(
    incident: dict[str, Any],
    settings: Settings,
    *,
    assignment_group: str | None = None,
    short_description: str | None = None,
    description: str | None = None,
) -> ServiceNowIncidentPayload:
    severity_map = settings.servicenow_priority_map.get(
        incident["severity"], {"impact": "3", "urgency": "3"}
    )
    return ServiceNowIncidentPayload(
        short_description=(
            short_description
            or f"[EntraGuard AI] {incident['severity']} - {incident['title']}"
        )[:160],
        description=description or format_ticket_description(incident),
        category=settings.servicenow_default_category,
        subcategory=settings.servicenow_default_subcategory,
        assignment_group=assignment_group or settings.servicenow_assignment_group,
        impact=str(severity_map.get("impact", "3")),
        urgency=str(severity_map.get("urgency", "3")),
        correlation_id=incident["id"],
        state=ENTRAGUARD_TO_SERVICENOW_STATE.get(incident["status"], "1"),
    )


def ticket_preview(incident: dict[str, Any], settings: Settings) -> dict[str, Any]:
    payload = build_payload(incident, settings)
    return {
        "short_description": payload.short_description,
        "description": payload.description,
        "assignment_group": payload.assignment_group,
        "category": payload.category,
        "subcategory": payload.subcategory,
        "impact": payload.impact,
        "urgency": payload.urgency,
        "evidence_policy": "Generated only from verified incident evidence",
    }

