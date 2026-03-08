"""
GrantWeave — Export Service
Generates PDF and CSV exports of pre-filled grant applications.
"""

import csv
import io
import uuid
from typing import List, Optional
from datetime import datetime
import database
from models import GrantResult


# ─── CSV Export ────────────────────────────────────────────────────────────────

async def export_csv(session_id: str, grant_ids: Optional[List[str]] = None) -> bytes:
    """
    Export grants as CSV bytes.
    Includes: title, funder, amount, deadline, url, category, match_score, description.
    """
    grants = await database.list_grants(session_id=session_id)
    if grant_ids:
        grants = [g for g in grants if g["id"] in grant_ids]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "title", "funder", "amount", "deadline", "url",
        "category", "match_score", "description", "requirements", "status"
    ])
    writer.writeheader()
    for g in grants:
        writer.writerow({
            "title": g.get("title", ""),
            "funder": g.get("funder", ""),
            "amount": g.get("amount", ""),
            "deadline": g.get("deadline", ""),
            "url": g.get("url", ""),
            "category": g.get("category", ""),
            "match_score": g.get("match_score", 0),
            "description": (g.get("description") or "")[:200],
            "requirements": (g.get("requirements") or "")[:200],
            "status": g.get("status", "found")
        })

    return output.getvalue().encode("utf-8")


# ─── PDF Export ────────────────────────────────────────────────────────────────

async def export_pdf(session_id: str, grant_ids: Optional[List[str]] = None) -> bytes:
    """
    Generate a multi-page PDF with pre-filled grant application details.
    One grant per page, with all known fields populated.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        # Fallback: return a minimal PDF placeholder
        return b"%PDF-1.4\n1 0 obj\n<< >>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<< /Root 1 0 R /Size 1 >>\nstartxref\n18\n%%EOF"

    grants = await database.list_grants(session_id=session_id)
    if grant_ids:
        grants = [g for g in grants if g["id"] in grant_ids]

    session = await database.get_session(session_id)
    org_id = session.get("org_id") if session else None
    org = await database.get_org_profile(org_id) if org_id else {}

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ── Cover page ──
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_fill_color(15, 23, 42)  # dark background
    pdf.rect(0, 0, 210, 60, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(20)
    pdf.cell(0, 12, "GrantWeave — Grant Application Package", align="C", ln=True)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"Organization: {org.get('name', 'N/A')}", align="C", ln=True)
    pdf.cell(0, 8, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d')}", align="C", ln=True)
    pdf.cell(0, 8, f"Total Grants: {len(grants)}", align="C", ln=True)

    # ── One page per grant ──
    for i, g in enumerate(grants, 1):
        pdf.add_page()
        pdf.set_text_color(0, 0, 0)

        # Header band
        pdf.set_fill_color(99, 102, 241)  # indigo
        pdf.rect(0, 0, 210, 20, "F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_y(5)
        pdf.cell(0, 10, f"Grant #{i}: {g.get('title', 'Untitled')[:70]}", align="C", ln=True)

        pdf.set_text_color(0, 0, 0)
        pdf.set_y(28)

        def field(label: str, value: str, bold: bool = False) -> None:
            pdf.set_font("Helvetica", "B" if bold else "", 10)
            pdf.cell(50, 7, label + ":", ln=False)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 7, str(value or "Not specified"))

        field("Funder", g.get("funder", ""))
        field("Award Amount", g.get("amount", ""))
        field("Deadline", g.get("deadline", ""))
        field("Category", g.get("category", ""))
        field("Match Score", f"{g.get('match_score', 0):.1f} / 10")
        field("Website", g.get("url", ""))
        pdf.ln(4)
        field("Description", g.get("description", "")[:500])
        pdf.ln(4)
        field("Requirements", g.get("requirements", "")[:500])
        pdf.ln(6)

        # Pre-fill section
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(240, 240, 255)
        pdf.cell(0, 8, "   Pre-Filled Application Fields", fill=True, ln=True)
        pdf.ln(2)
        field("Applicant Organization", org.get("name", ""))
        field("EIN / Tax ID", org.get("ein", ""))
        field("Mission Statement", org.get("mission", "")[:300])
        field("Primary Focus Areas", ", ".join(org.get("focus_areas", [])))
        field("Location", org.get("location", ""))
        field("Annual Budget", f"${org.get('budget', 0):,.0f}" if org.get("budget") else "")
        field("Year Founded", str(org.get("founded", "")))
        field("Website", org.get("website", ""))

    return bytes(pdf.output())
