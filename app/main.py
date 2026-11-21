from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings
from app.database import Database, seed_demo_data
from app.models import CommentRequest, CreateServiceNowRequest, IncidentStatusRequest, UpdateServiceNowRequest
from providers.servicenow.models import ServiceNowError
from providers.servicenow.service import ServiceNowIntegrationService


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


def _actor(value: str | None) -> str:
    return (value or "Alex Morgan").strip()[:120] or "Security Analyst"


def create_app(*, settings: Settings | None = None, database: Database | None = None) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    resolved_database = database or Database(resolved_settings.database_path)
    resolved_database.init()
    seed_demo_data(resolved_database)
    integration = ServiceNowIntegrationService(resolved_settings, resolved_database)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if resolved_settings.servicenow_auto_create and resolved_settings.servicenow_enabled:
            ranks = {"Informational": 0, "Low": 1, "Medium": 2, "High": 3, "Critical": 4}
            minimum = ranks.get(resolved_settings.servicenow_auto_create_min_severity, 4)
            for incident in resolved_database.list_incidents():
                if ranks.get(incident["severity"], 0) >= minimum and not incident.get("service_now_sys_id"):
                    try:
                        integration.create_incident(incident["id"], actor="EntraGuard Automation", automatic=True)
                    except ServiceNowError:
                        pass
        yield

    app = FastAPI(
        title="EntraGuard AI",
        version="1.0.0",
        description="Identity security incident investigation with ServiceNow integration",
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings
    app.state.database = resolved_database
    app.state.servicenow = integration

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {
            "status": "healthy",
            "servicenow": {
                "enabled": resolved_settings.servicenow_enabled,
                "mode": resolved_settings.servicenow_mode,
                "auto_create": resolved_settings.servicenow_auto_create,
                "configured": resolved_settings.servicenow_mode == "mock" or bool(resolved_settings.servicenow_instance_url),
                "assignment_groups": resolved_settings.servicenow_assignment_groups,
                "default_assignment_group": resolved_settings.servicenow_assignment_group,
            },
        }

    @app.get("/api/incidents")
    def list_incidents() -> dict[str, Any]:
        incidents = resolved_database.list_incidents()
        return {"items": incidents, "count": len(incidents)}

    @app.get("/api/incidents/{incident_id}")
    def get_incident(incident_id: str) -> dict[str, Any]:
        incident = resolved_database.get_incident(incident_id)
        if not incident:
            raise HTTPException(404, "Incident not found.")
        return incident

    @app.patch("/api/incidents/{incident_id}/status")
    def set_incident_status(
        incident_id: str,
        body: IncidentStatusRequest,
        x_analyst: Annotated[str | None, Header()] = None,
    ) -> dict[str, Any]:
        try:
            return integration.sync_entraguard_status(incident_id, body.status, actor=_actor(x_analyst))
        except KeyError:
            raise HTTPException(404, "Incident not found.") from None
        except ServiceNowError as exc:
            raise HTTPException(502 if exc.retryable else 400, str(exc)) from None

    @app.get("/api/incidents/{incident_id}/servicenow/preview")
    def preview_servicenow(incident_id: str) -> dict[str, Any]:
        try:
            return integration.preview(incident_id)
        except KeyError:
            raise HTTPException(404, "Incident not found.") from None

    @app.post("/api/incidents/{incident_id}/servicenow")
    def create_servicenow(
        incident_id: str,
        body: CreateServiceNowRequest,
        x_analyst: Annotated[str | None, Header()] = None,
    ) -> dict[str, Any]:
        try:
            return integration.create_incident(
                incident_id,
                actor=_actor(x_analyst),
                assignment_group=body.assignment_group,
                short_description=body.short_description,
                description=body.description,
            )
        except KeyError:
            raise HTTPException(404, "Incident not found.") from None
        except ServiceNowError as exc:
            raise HTTPException(503 if exc.retryable else 400, str(exc)) from None

    @app.get("/api/incidents/{incident_id}/servicenow")
    def get_servicenow(
        incident_id: str,
        sync: bool = Query(default=True),
        x_analyst: Annotated[str | None, Header()] = None,
    ) -> dict[str, Any]:
        try:
            return integration.get_incident(incident_id, actor=_actor(x_analyst), synchronize=sync)
        except KeyError:
            raise HTTPException(404, "Incident not found.") from None
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from None
        except ServiceNowError as exc:
            raise HTTPException(503 if exc.retryable else 400, str(exc)) from None

    @app.patch("/api/incidents/{incident_id}/servicenow")
    def update_servicenow(
        incident_id: str,
        body: UpdateServiceNowRequest,
        x_analyst: Annotated[str | None, Header()] = None,
    ) -> dict[str, Any]:
        try:
            return integration.update_incident(incident_id, body.model_dump(exclude_none=True), actor=_actor(x_analyst))
        except KeyError:
            raise HTTPException(404, "Incident not found.") from None
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from None
        except ServiceNowError as exc:
            raise HTTPException(503 if exc.retryable else 400, str(exc)) from None

    @app.post("/api/incidents/{incident_id}/servicenow/comment")
    def comment_servicenow(
        incident_id: str,
        body: CommentRequest,
        x_analyst: Annotated[str | None, Header()] = None,
    ) -> dict[str, Any]:
        try:
            return integration.add_comment(incident_id, body.comment, actor=_actor(x_analyst))
        except KeyError:
            raise HTTPException(404, "Incident not found.") from None
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from None
        except ServiceNowError as exc:
            raise HTTPException(503 if exc.retryable else 400, str(exc)) from None

    @app.get("/api/incidents/{incident_id}/audit")
    def incident_audit(incident_id: str) -> dict[str, Any]:
        if not resolved_database.get_incident(incident_id):
            raise HTTPException(404, "Incident not found.")
        items = resolved_database.list_audit(incident_id)
        return {"items": items, "count": len(items)}

    @app.post("/api/demo/reset")
    def reset_demo(x_analyst: Annotated[str | None, Header()] = None) -> dict[str, Any]:
        if resolved_settings.servicenow_mode != "mock":
            raise HTTPException(403, "Demo reset is available only in mock mode.")
        resolved_database.clear_demo_data()
        seed_demo_data(resolved_database)
        return {"reset": True, "actor": _actor(x_analyst)}

    @app.get("/mock-servicenow/incidents/{sys_id}", response_class=HTMLResponse)
    def mock_servicenow_page(sys_id: str) -> str:
        if resolved_settings.servicenow_mode != "mock":
            raise HTTPException(404, "Not found.")
        record = resolved_database.get_mock_record(sys_id)
        if not record:
            raise HTTPException(404, "Mock incident not found.")
        # This server-rendered mock page is intentionally simple and escapes values by replacing HTML delimiters.
        safe = {key: str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") for key, value in record.items()}
        return f"""<!doctype html><html><head><meta charset='utf-8'><title>{safe['number']} · Mock ServiceNow</title>
        <style>body{{margin:0;font:14px Inter,Segoe UI,sans-serif;background:#f5f7f8;color:#172b34}}header{{background:#14333d;color:white;padding:20px 8%}}main{{max-width:980px;margin:36px auto;background:white;border:1px solid #dfe5e8;border-radius:8px;padding:28px;box-shadow:0 8px 28px #14333d14}}.label{{color:#607680;font-size:12px;text-transform:uppercase;letter-spacing:.08em;margin-top:22px}}h1{{margin:4px 0 0}}pre{{white-space:pre-wrap;font:14px/1.6 Segoe UI,sans-serif;background:#f7f9fa;padding:18px;border-radius:6px}}.mock{{background:#d7f3ea;color:#0b5945;padding:5px 9px;border-radius:99px;font-weight:700}}</style></head>
        <body><header><strong>ServiceNow</strong> <span class='mock'>MOCK INSTANCE</span></header><main><div class='label'>Incident</div><h1>{safe['number']}</h1><div class='label'>Short description</div><h2>{safe['short_description']}</h2><div class='label'>State</div><p>{safe['state']}</p><div class='label'>Assignment group</div><p>{safe['assignment_group']}</p><div class='label'>Description</div><pre>{safe['description']}</pre></main></body></html>"""

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()

