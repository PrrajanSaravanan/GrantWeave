"""
GrantWeave — FastAPI Main Application
All routes, SSE streaming, WebSocket team handoff, and CORS.

Routes:
  GET  /api/health               — Health check
  POST /api/onboard              — Manual org profile creation
  POST /api/onboard/pdf          — Upload org PDF for profile extraction
  GET  /api/orgs                 — List org profiles
  GET  /api/orgs/{org_id}        — Get single org profile
  POST /api/hunt                 — Start grant hunt (SSE stream)
  GET  /api/sessions             — List all sessions
  GET  /api/sessions/{id}        — Get single session
  GET  /api/grants               — List all grants (optionally filter by session)
  GET  /api/evo-log              — EvoForge mutation log
  GET  /api/templates            — Akasha Ledger templates
  POST /api/export               — Download PDF or CSV
  GET  /api/wrapped/{org_id}     — GrantWeave Wrapped report
  GET  /api/share/{token}        — Resolve share token → session
  WS   /ws/team/{session_id}     — Team handoff WebSocket
"""

import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

import database
import onboarding
import akasha_ledger
import export_service
import wrapped_service
from models import OrgProfileCreate, HuntRequest, ExportRequest
from orchestrator import hunt_grants
from websocket_manager import ws_manager

load_dotenv()

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")


# ─── Lifespan (startup / shutdown) ────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB and seed Akasha templates on startup."""
    await database.init_db()
    await akasha_ledger.seed_starter_templates()
    print("✅ GrantWeave AetherForge backend ready")
    yield
    print("👋 GrantWeave shutting down")


# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="GrantWeave AetherForge API",
    description="Autonomous grant-hunting powered by the AetherForge kernel and TinyFish agents",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "GrantWeave AetherForge",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# ─── Onboarding ───────────────────────────────────────────────────────────────

@app.post("/api/onboard")
async def onboard_manual(org: OrgProfileCreate):
    """Create an org profile from manual form data."""
    profile = await onboarding.create_profile_manual(org)
    return {"success": True, "org": profile.model_dump()}


@app.post("/api/onboard/pdf")
async def onboard_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF (annual report, IRS determination letter, etc.)
    and extract an org profile from it automatically.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted")

    pdf_bytes = await file.read()
    profile, snippet = await onboarding.create_profile_from_pdf(pdf_bytes)
    return {
        "success": True,
        "org": profile.model_dump(),
        "extracted_text_snippet": snippet
    }


@app.get("/api/orgs")
async def list_orgs():
    profiles = await onboarding.list_profiles()
    return {"orgs": [p.model_dump() for p in profiles]}


@app.get("/api/orgs/{org_id}")
async def get_org(org_id: str):
    profile = await onboarding.get_profile(org_id)
    if not profile:
        raise HTTPException(404, f"Org '{org_id}' not found")
    return profile.model_dump()


# ─── Grant Hunting (SSE) ──────────────────────────────────────────────────────

@app.post("/api/hunt")
async def start_hunt(req: HuntRequest):
    """
    Begin a grant hunt. Returns a Server-Sent Events stream.
    The client should open this endpoint with EventSource:

        const es = new EventSource('/api/hunt');
        es.onmessage = (e) => { ... }

    However since we need to POST a body we use the fetch + readable stream approach.
    Events: STARTED, SCANNING, MATCH_FOUND, STREAMING_URL, EVO_MUTATION,
            EVO_RESULT, AKASHA_HIT, RESUMED, COMPLETE, ERROR
    """
    # Verify org exists
    org = await database.get_org_profile(req.org_id)
    if not org:
        raise HTTPException(404, f"Org '{req.org_id}' not found")

    session_id = str(uuid.uuid4())
    share_token = str(uuid.uuid4())[:8]

    # Create session record
    await database.create_session({
        "id": session_id,
        "org_id": req.org_id,
        "command": req.command,
        "status": "running",
        "share_token": share_token
    })

    async def event_stream():
        try:
            async for chunk in hunt_grants(session_id, req.org_id, req.command):
                yield chunk
        except Exception as exc:
            import json
            yield f"data: {json.dumps({'event': 'ERROR', 'session_id': session_id, 'message': str(exc)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Session-Id": session_id,
            "X-Share-Token": share_token,
            "Access-Control-Expose-Headers": "X-Session-Id, X-Share-Token"
        }
    )


# ─── Sessions ─────────────────────────────────────────────────────────────────

@app.get("/api/sessions")
async def list_sessions(limit: int = Query(20, le=100)):
    sessions = await database.list_sessions(limit=limit)
    return {"sessions": sessions}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    session = await database.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session


# ─── Grants ───────────────────────────────────────────────────────────────────

@app.get("/api/grants")
async def list_grants(session_id: Optional[str] = Query(None)):
    grants = await database.list_grants(session_id=session_id)
    return {"grants": grants, "total": len(grants)}


# ─── EvoLog ───────────────────────────────────────────────────────────────────

@app.get("/api/evo-log")
async def get_evo_log(
    session_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200)
):
    entries = await database.list_evo_log(session_id=session_id, limit=limit)
    return {"entries": entries, "total": len(entries)}


# ─── Akasha Templates ─────────────────────────────────────────────────────────

@app.get("/api/templates")
async def list_templates(category: Optional[str] = Query(None)):
    templates = await akasha_ledger.list_templates(category=category)
    return {"templates": [t.model_dump() for t in templates]}


# ─── Export ───────────────────────────────────────────────────────────────────

@app.post("/api/export")
async def export_grants(req: ExportRequest):
    """
    Export grant applications.
    Returns a PDF or CSV file as a download.
    """
    session = await database.get_session(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    if req.format == "csv":
        data = await export_service.export_csv(req.session_id, req.grant_ids)
        filename = f"grantweave_grants_{req.session_id[:8]}.csv"
        return Response(
            content=data,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    else:
        data = await export_service.export_pdf(req.session_id, req.grant_ids)
        filename = f"grantweave_applications_{req.session_id[:8]}.pdf"
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )


# ─── Wrapped ──────────────────────────────────────────────────────────────────

@app.get("/api/wrapped/{org_id}")
async def get_wrapped(org_id: str):
    """Generate (or retrieve cached) GrantWeave Wrapped weekly report."""
    # Check for cached report first
    cached = await database.get_wrapped_report(org_id)
    if cached:
        return cached
    # Generate fresh
    report = await wrapped_service.generate_wrapped(org_id)
    return report.model_dump()


# ─── Team Handoff ─────────────────────────────────────────────────────────────

@app.get("/api/share/{token}")
async def resolve_share(token: str):
    """Resolve a share token to a session."""
    session = await database.get_session_by_token(token)
    if not session:
        raise HTTPException(404, "Share link not found or expired")
    return session


@app.websocket("/ws/team/{session_id}")
async def team_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket for real-time team handoff.
    All clients watching the same session_id receive broadcast messages.
    """
    await ws_manager.connect(session_id, websocket)
    # Announce new peer to all others
    await ws_manager.broadcast(session_id, {
        "event": "PEER_JOINED",
        "peers": ws_manager.peer_count(session_id)
    })

    try:
        while True:
            # Relay messages from this client to all peers
            data = await websocket.receive_json()
            data["sender"] = str(id(websocket))
            await ws_manager.broadcast(session_id, data)
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id, websocket)
        await ws_manager.broadcast(session_id, {
            "event": "PEER_LEFT",
            "peers": ws_manager.peer_count(session_id)
        })
