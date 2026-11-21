# EntraGuard AI — ServiceNow incident integration

An end-to-end identity-security incident operations POC. Analysts can investigate correlated Microsoft Entra signals, review an evidence-grounded ticket summary, and create a linked ServiceNow incident with explicit human approval.

The repository is intentionally runnable without a ServiceNow license. `SERVICENOW_MODE=mock` persists realistic `INC0010001`-style records and provides a mock ServiceNow incident view.

## Run locally

```powershell
Copy-Item .env.example .env
uv run uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The seeded critical scenario is `EG-2026-0045` with a risk score of 96.

Run the automated checks with:

```powershell
uv run python -m pytest -q
```

If you prefer `pip`, install `requirements.txt` and run the same `uvicorn` module directly.

## Demonstrated workflow

1. Open the critical privileged-account-takeover incident.
2. Select **Raise ServiceNow ticket**.
3. Review the verified-evidence-only SOC summary and choose an assignment group.
4. Create the ticket. Its number, status, assignment group, timestamps, URL, and system ID are persisted on the EntraGuard incident.
5. Open the mock ServiceNow record or send an investigation work note.
6. Change EntraGuard status to `Investigating` or `Resolved`; the linked ServiceNow state is synchronized without a polling loop.
7. Review every create, update, comment, synchronization, duplicate prevention, or failure action in the audit trail.

To replay the demo, call `POST /api/demo/reset` while in mock mode, or remove `entraguard.db` while the server is stopped.

## ServiceNow configuration

Copy `.env.example` and set `SERVICENOW_MODE=live` with an instance URL. OAuth client credentials are preferred; basic credentials are supported for development instances. Credentials are consumed only by the backend and the health/config response exposes only safe flags.

ServiceNow usually calculates priority from `impact` and `urgency`; the configurable `SERVICENOW_PRIORITY_MAP` therefore maps EntraGuard severities to those inputs instead of writing a calculated priority directly. Assignment group values may be display names in mock mode; for live instances, use values accepted by that instance (commonly a group sys_id).

Automatic creation is off by default. If explicitly enabled with `SERVICENOW_AUTO_CREATE=true`, incidents at or above `SERVICENOW_AUTO_CREATE_MIN_SEVERITY` are created at startup with duplicate protection, rate limiting, bounded retries, failure metadata, and audit events.

## API

- `GET /api/incidents` and `GET /api/incidents/{incidentId}`
- `PATCH /api/incidents/{incidentId}/status`
- `GET /api/incidents/{incidentId}/servicenow/preview`
- `POST /api/incidents/{incidentId}/servicenow`
- `GET /api/incidents/{incidentId}/servicenow`
- `PATCH /api/incidents/{incidentId}/servicenow`
- `POST /api/incidents/{incidentId}/servicenow/comment`
- `GET /api/incidents/{incidentId}/audit`
- `GET /api/health`

Interactive API documentation is at `/docs`.

## Architecture

```text
app/
  config.py        environment-only configuration
  database.py      SQLite incidents, mock records, counters, and audit log
  main.py          FastAPI routes and safe error boundaries
providers/
  servicenow/
    client.py      mock and live REST/OAuth clients
    models.py      provider contracts
    mapper.py      evidence-grounded content and severity/state mapping
    service.py     duplicate protection, retry/rate-limit, sync, and auditing
static/            analyst operations dashboard
tests/             integration workflow tests
```

The ServiceNow provider does not participate in detection or correlation logic. A ServiceNow outage never removes or mutates the underlying EntraGuard security incident.
