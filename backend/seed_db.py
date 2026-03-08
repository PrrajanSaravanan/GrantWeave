"""
GrantWeave — Database Seeder
Pre-populates the SQLite database with 2–3 demo runs so the app
looks great on first launch (no empty state).

Run: python seed_db.py
"""

import asyncio
import uuid
from datetime import datetime, timedelta
import database
import akasha_ledger


async def seed() -> None:
    print("[Seed] Initializing database…")
    await database.init_db()

    # ── 1. Demo org profiles ───────────────────────────────────────────────────
    orgs = [
        {
            "id": "demo-org-001",
            "name": "Bright Futures Foundation",
            "mission": "Empowering underserved youth through STEM education and mentorship programs.",
            "ein": "82-1234567",
            "focus_areas": ["education", "stem", "youth"],
            "location": "San Francisco, CA",
            "budget": 250000.0,
            "founded": 2015,
            "website": "https://brightfutures.example.org"
        },
        {
            "id": "demo-org-002",
            "name": "GreenEarth Alliance",
            "mission": "Protecting biodiversity and combating climate change through community action.",
            "ein": "45-9876543",
            "focus_areas": ["environment", "climate", "community"],
            "location": "Austin, TX",
            "budget": 180000.0,
            "founded": 2012,
            "website": "https://greenearth.example.org"
        },
        {
            "id": "demo-org-003",
            "name": "HealthBridge Clinic",
            "mission": "Providing free and low-cost healthcare to uninsured adults in rural communities.",
            "ein": "61-5432109",
            "focus_areas": ["healthcare", "rural", "disability"],
            "location": "Nashville, TN",
            "budget": 320000.0,
            "founded": 2008,
            "website": "https://healthbridge.example.org"
        }
    ]
    for org in orgs:
        await database.save_org_profile(org)
    print(f"[Seed] Created {len(orgs)} org profiles")

    # ── 2. Demo sessions & grants ──────────────────────────────────────────────
    sessions_data = [
        {
            "id": "demo-session-001",
            "org_id": "demo-org-001",
            "command": "Find STEM education grants in California for nonprofits",
            "status": "completed",
            "grants_found": 4,
            "share_token": "share-abc123"
        },
        {
            "id": "demo-session-002",
            "org_id": "demo-org-002",
            "command": "Environmental conservation grants for climate initiatives in Texas",
            "status": "completed",
            "grants_found": 3,
            "share_token": "share-def456"
        },
        {
            "id": "demo-session-003",
            "org_id": "demo-org-003",
            "command": "Rural healthcare grants for free clinics serving uninsured adults",
            "status": "completed",
            "grants_found": 5,
            "share_token": "share-ghi789"
        }
    ]
    for s in sessions_data:
        await database.create_session(s)
        await database.update_session(s["id"], {
            "status": s["status"],
            "completed_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "grants_found": s["grants_found"]
        })
    print(f"[Seed] Created {len(sessions_data)} sessions")

    # ── 3. Demo grant results ──────────────────────────────────────────────────
    grants = [
        # Session 001 — STEM Education
        {
            "id": str(uuid.uuid4()), "session_id": "demo-session-001",
            "title": "NSF STEM Education Grant Program",
            "funder": "National Science Foundation",
            "amount": "$150,000 – $500,000",
            "deadline": "2026-04-15",
            "url": "https://www.nsf.gov/funding/pgm_summ.jsp?pims_id=5741",
            "category": "federal",
            "match_score": 9.2,
            "description": "NSF's STEM Ed program funds innovative research-based education initiatives targeting K-12 and undergraduate populations.",
            "requirements": "501(c)(3) status required. Must serve at least 200 students annually.",
            "status": "found"
        },
        {
            "id": str(uuid.uuid4()), "session_id": "demo-session-001",
            "title": "California STEM Pathways Initiative",
            "funder": "California Department of Education",
            "amount": "$75,000 – $200,000",
            "deadline": "2026-03-30",
            "url": "https://www.cde.ca.gov/fg/fo/profile.asp?id=5701",
            "category": "state",
            "match_score": 8.7,
            "description": "Supports California nonprofits delivering STEM programming to underrepresented youth ages 10–18.",
            "requirements": "California-based organization. Focus on underrepresented groups required.",
            "status": "found"
        },
        {
            "id": str(uuid.uuid4()), "session_id": "demo-session-001",
            "title": "Google.org STEM Education Fund",
            "funder": "Google.org",
            "amount": "$50,000 – $250,000",
            "deadline": "2026-05-01",
            "url": "https://www.google.org/our-work/education/",
            "category": "foundation",
            "match_score": 8.1,
            "description": "Google.org invests in nonprofits using technology to improve STEM access and outcomes for underserved communities.",
            "requirements": "Tech-forward approach required. Impact measurement plan mandatory.",
            "status": "found"
        },
        {
            "id": str(uuid.uuid4()), "session_id": "demo-session-001",
            "title": "STEM Equity Accelerator — Verizon Foundation",
            "funder": "Verizon Foundation",
            "amount": "$25,000 – $100,000",
            "deadline": "2026-06-15",
            "url": "https://www.verizon.com/about/responsibility/foundation",
            "category": "corporate",
            "match_score": 7.5,
            "description": "Verizon Foundation funds digital literacy and STEM equity programs for underserved K-12 students.",
            "requirements": "Must operate in Verizon service area. Annual report required.",
            "status": "found"
        },
        # Session 002 — Environment
        {
            "id": str(uuid.uuid4()), "session_id": "demo-session-002",
            "title": "EPA Environmental Justice Collaborative Problem-Solving Grant",
            "funder": "U.S. Environmental Protection Agency",
            "amount": "$100,000 – $300,000",
            "deadline": "2026-04-01",
            "url": "https://www.epa.gov/environmentaljustice/environmental-justice-collaborative-problem-solving-cooperative",
            "category": "federal",
            "match_score": 9.0,
            "description": "Supports organizations working to address environmental issues affecting disadvantaged communities.",
            "requirements": "501(c)(3) or tribal organization. Community partnership required.",
            "status": "found"
        },
        {
            "id": str(uuid.uuid4()), "session_id": "demo-session-002",
            "title": "Texas Commission on Environmental Quality Grant",
            "funder": "Texas Commission on Environmental Quality",
            "amount": "$50,000 – $150,000",
            "deadline": "2026-05-15",
            "url": "https://www.tceq.texas.gov/grants",
            "category": "state",
            "match_score": 8.3,
            "description": "TCEQ funds projects that reduce air pollution and improve environmental quality across Texas.",
            "requirements": "Texas nonprofit or municipal entity. Air quality focus preferred.",
            "status": "found"
        },
        {
            "id": str(uuid.uuid4()), "session_id": "demo-session-002",
            "title": "National Geographic Society Conservation Grant",
            "funder": "National Geographic Society",
            "amount": "$15,000 – $50,000",
            "deadline": "2026-03-15",
            "url": "https://www.nationalgeographic.org/society/grants-and-investments/",
            "category": "foundation",
            "match_score": 7.8,
            "description": "Funds field research and conservation education projects with measurable biodiversity impact.",
            "requirements": "Must have a field conservation component. Global focus accepted.",
            "status": "found"
        },
        # Session 003 — Healthcare
        {
            "id": str(uuid.uuid4()), "session_id": "demo-session-003",
            "title": "HRSA Rural Health Care Services Outreach Grant",
            "funder": "Health Resources & Services Administration",
            "amount": "$200,000 – $500,000",
            "deadline": "2026-04-30",
            "url": "https://www.hrsa.gov/grants/find-funding/HRSA-26-001",
            "category": "federal",
            "match_score": 9.5,
            "description": "HRSA funds rural health organizations expanding access to primary care services for uninsured populations.",
            "requirements": "Located in a HRSA-designated rural area. Sliding-scale fee structure required.",
            "status": "found"
        },
        {
            "id": str(uuid.uuid4()), "session_id": "demo-session-003",
            "title": "Tennessee State Health Access Program",
            "funder": "Tennessee Department of Health",
            "amount": "$75,000 – $200,000",
            "deadline": "2026-03-20",
            "url": "https://www.tn.gov/health/health-system-improvement/grants.html",
            "category": "state",
            "match_score": 8.9,
            "description": "Supports free clinic operations serving uninsured adults in Tennessee communities.",
            "requirements": "Tennessee nonprofit. Must serve 300+ uninsured patients annually.",
            "status": "found"
        },
        {
            "id": str(uuid.uuid4()), "session_id": "demo-session-003",
            "title": "Robert Wood Johnson Foundation Health Care Access Grant",
            "funder": "Robert Wood Johnson Foundation",
            "amount": "$100,000 – $400,000",
            "deadline": "2026-05-31",
            "url": "https://www.rwjf.org/en/grants/active-funding-opportunities.html",
            "category": "foundation",
            "match_score": 9.1,
            "description": "RWJF's signature grant for organizations building a culture of health through equitable healthcare access.",
            "requirements": "Demonstrated health equity focus. Community health assessment required.",
            "status": "found"
        },
        {
            "id": str(uuid.uuid4()), "session_id": "demo-session-003",
            "title": "UnitedHealth Foundation Community Health Grant",
            "funder": "UnitedHealth Foundation",
            "amount": "$25,000 – $100,000",
            "deadline": "2026-06-30",
            "url": "https://www.unitedhealthgroup.com/giving-back/grants.html",
            "category": "corporate",
            "match_score": 7.9,
            "description": "Funds health nonprofits improving community health outcomes and reducing disparities.",
            "requirements": "U.S. nonprofits only. Data-driven outcomes measurement required.",
            "status": "found"
        },
        {
            "id": str(uuid.uuid4()), "session_id": "demo-session-003",
            "title": "CDC Rural Health Initiative Grant",
            "funder": "Centers for Disease Control and Prevention",
            "amount": "$150,000 – $350,000",
            "deadline": "2026-04-10",
            "url": "https://www.cdc.gov/grants/index.html",
            "category": "federal",
            "match_score": 8.6,
            "description": "CDC initiative to strengthen rural health infrastructure and expand preventive care programs.",
            "requirements": "Rural designation required. Partnership with local health dept preferred.",
            "status": "found"
        }
    ]
    for g in grants:
        await database.save_grant(g)
    print(f"[Seed] Created {len(grants)} grant results")

    # ── 4. Demo EvoLog entries ─────────────────────────────────────────────────
    evo_entries = [
        {
            "id": str(uuid.uuid4()), "session_id": "demo-session-001",
            "attempt": 1,
            "original_goal": "Search grants.gov for STEM education grants in California",
            "mutated_goal": "Search grants.gov for STEM education grants in California. Navigate through ALL pages. Output JSON.",
            "strategy": "pagination_aware",
            "result": "success",
            "score": 7.5
        },
        {
            "id": str(uuid.uuid4()), "session_id": "demo-session-002",
            "attempt": 1,
            "original_goal": "Search EPA.gov for environmental conservation grants in Texas",
            "mutated_goal": "Before searching: close any cookie popups. Then search EPA.gov for environmental grants in Texas. Return JSON.",
            "strategy": "popup_handler",
            "result": "success",
            "score": 6.8
        },
        {
            "id": str(uuid.uuid4()), "session_id": "demo-session-002",
            "attempt": 2,
            "original_goal": "Search EPA.gov for environmental conservation grants in Texas",
            "mutated_goal": "If EPA.gov is unavailable try sam.gov and candid.org for environmental grants in Texas. Return JSON.",
            "strategy": "alternative_source",
            "result": "failure",
            "score": 2.1
        }
    ]
    for e in evo_entries:
        await database.save_evo_entry(e)
    print(f"[Seed] Created {len(evo_entries)} EvoLog entries")

    # ── 5. Seed Akasha starter templates ──────────────────────────────────────
    await akasha_ledger.seed_starter_templates()

    print("\n✅ Seed complete! Your GrantWeave demo data is ready.")
    print("   Run: uvicorn main:app --reload --port 8000")


if __name__ == "__main__":
    asyncio.run(seed())
