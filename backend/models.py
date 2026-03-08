"""
GrantWeave — Pydantic Models
All request/response schemas for the FastAPI backend.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime


# ─── Org Profile ───────────────────────────────────────────────────────────────

class OrgProfileCreate(BaseModel):
    name: str
    mission: Optional[str] = None
    ein: Optional[str] = None
    focus_areas: List[str] = []
    location: Optional[str] = None
    budget: Optional[float] = None
    founded: Optional[int] = None
    website: Optional[str] = None


class OrgProfile(OrgProfileCreate):
    id: str
    created_at: Optional[str] = None


# ─── Sessions ─────────────────────────────────────────────────────────────────

class HuntRequest(BaseModel):
    org_id: str
    command: str = Field(
        ...,
        description="Natural language grant-hunting command",
        example="Find STEM education grants in California for nonprofits"
    )


class Session(BaseModel):
    id: str
    org_id: Optional[str] = None
    command: str
    status: str = "pending"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    grants_found: int = 0
    share_token: Optional[str] = None


# ─── Grant Results ─────────────────────────────────────────────────────────────

class GrantResult(BaseModel):
    id: str
    session_id: str
    title: str
    funder: Optional[str] = None
    amount: Optional[str] = None
    deadline: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    match_score: float = 0.0
    description: Optional[str] = None
    requirements: Optional[str] = None
    status: str = "found"
    created_at: Optional[str] = None


# ─── EvoForge ─────────────────────────────────────────────────────────────────

class EvoLogEntry(BaseModel):
    id: str
    session_id: str
    attempt: int
    original_goal: str
    mutated_goal: str
    strategy: str
    result: str = "pending"   # pending | success | failure
    score: float = 0.0
    created_at: Optional[str] = None


# ─── Akasha Ledger ─────────────────────────────────────────────────────────────

class AkashaTemplate(BaseModel):
    id: str
    name: str
    goal_template: str
    category: Optional[str] = None
    success_count: int = 0
    avg_score: float = 0.0
    last_used: Optional[str] = None
    created_at: Optional[str] = None


# ─── SSE Events ───────────────────────────────────────────────────────────────

class SSEEvent(BaseModel):
    event: str            # STARTED | SCANNING | MATCH_FOUND | EVO_MUTATION | STREAMING_URL | COMPLETE | ERROR
    session_id: str
    data: Dict[str, Any] = {}


# ─── Export ───────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    session_id: str
    format: str = "pdf"   # pdf | csv
    grant_ids: Optional[List[str]] = None   # None = export all from session


# ─── Wrapped Report ───────────────────────────────────────────────────────────

class WrappedReport(BaseModel):
    id: str
    org_id: Optional[str] = None
    week_of: str
    sessions_run: int = 0
    grants_found: int = 0
    best_match: Optional[str] = None
    mutations_run: int = 0
    data: Dict[str, Any] = {}
    created_at: Optional[str] = None


# ─── TinyFish raw SSE event ───────────────────────────────────────────────────

class TFEvent(BaseModel):
    """Parsed TinyFish SSE event."""
    kind: str              # STARTED | PROGRESS | STREAMING_URL | COMPLETE | ERROR
    run_id: Optional[str] = None
    message: Optional[str] = None
    streaming_url: Optional[str] = None
    result_json: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
