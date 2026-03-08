"""
GrantWeave — Onboarding Service
Parses org profiles from uploaded PDFs or accepts manual form input.
Uses PyMuPDF for PDF text extraction and regex pattern matching to
pull structured fields from unstructured documents.
"""

import re
import uuid
from typing import Optional, Dict, Any, Tuple
from models import OrgProfile, OrgProfileCreate
import database


# ─── PDF Parsing ───────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF file using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except ImportError:
        return ""
    except Exception as exc:
        print(f"[Onboarding] PDF parse error: {exc}")
        return ""


def parse_org_from_text(text: str) -> Dict[str, Any]:
    """
    Heuristic extraction of org profile fields from raw PDF text.
    Returns a partial OrgProfile dict (missing fields = None).
    """
    result: Dict[str, Any] = {}

    # Org name: first non-empty line longer than 5 chars
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines:
        result["name"] = lines[0][:120]

    # EIN: 12-3456789 pattern
    ein_match = re.search(r'\b\d{2}-\d{7}\b', text)
    if ein_match:
        result["ein"] = ein_match.group()

    # Website
    web_match = re.search(r'https?://\S+', text)
    if web_match:
        result["website"] = web_match.group().rstrip('.,)')

    # Mission / purpose — look for keywords
    mission_patterns = [
        r'(?:mission|purpose|vision)[:\s]+([^\n]{20,300})',
        r'(?:we are|our organization)[:\s]+([^\n]{20,300})'
    ]
    for pat in mission_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["mission"] = m.group(1).strip()
            break

    # Founded year
    year_match = re.search(r'\b(19|20)\d{2}\b', text)
    if year_match:
        result["founded"] = int(year_match.group())

    # Location (City, State pattern)
    loc_match = re.search(r'\b([A-Z][a-z]+(?: [A-Z][a-z]+)*),\s*([A-Z]{2})\b', text)
    if loc_match:
        result["location"] = loc_match.group()

    # Focus areas — look for sector keywords
    FOCUS_KEYWORDS = [
        "education", "healthcare", "stem", "environment", "arts",
        "housing", "food security", "workforce", "mental health",
        "disability", "veterans", "youth", "climate", "technology"
    ]
    found_focus = [kw for kw in FOCUS_KEYWORDS if kw in text.lower()]
    if found_focus:
        result["focus_areas"] = found_focus[:5]

    return result


# ─── Profile CRUD ─────────────────────────────────────────────────────────────

async def create_profile_from_pdf(pdf_bytes: bytes) -> Tuple[OrgProfile, str]:
    """
    Parse a PDF, create and persist an OrgProfile.
    Returns (profile, extracted_text_snippet).
    """
    text = extract_text_from_pdf(pdf_bytes)
    parsed = parse_org_from_text(text)

    profile_id = str(uuid.uuid4())
    profile_data = {
        "id": profile_id,
        "name": parsed.get("name", "Unknown Organization"),
        "mission": parsed.get("mission"),
        "ein": parsed.get("ein"),
        "focus_areas": parsed.get("focus_areas", []),
        "location": parsed.get("location"),
        "budget": None,
        "founded": parsed.get("founded"),
        "website": parsed.get("website")
    }

    await database.save_org_profile(profile_data)
    return OrgProfile(**profile_data), text[:500]


async def create_profile_manual(org: OrgProfileCreate) -> OrgProfile:
    """Create and persist an OrgProfile from manual form data."""
    profile_id = str(uuid.uuid4())
    profile_data = {"id": profile_id, **org.model_dump()}
    await database.save_org_profile(profile_data)
    return OrgProfile(**profile_data)


async def get_profile(org_id: str) -> Optional[OrgProfile]:
    row = await database.get_org_profile(org_id)
    return OrgProfile(**row) if row else None


async def list_profiles() -> list:
    rows = await database.list_org_profiles()
    return [OrgProfile(**r) for r in rows]
