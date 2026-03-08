"""
GrantWeave — Akasha Ledger
Permanent memory of successful goal templates and mutation strategies.
When a goal succeeds, it's stored here so future sessions reuse proven approaches.
"""

import uuid
from typing import Optional, List, Dict, Any
import database
from models import AkashaTemplate


async def save_template(
    name: str,
    goal_template: str,
    category: str,
    score: float
) -> AkashaTemplate:
    """Persist a successful goal template."""
    template = AkashaTemplate(
        id=str(uuid.uuid4()),
        name=name,
        goal_template=goal_template,
        category=category,
        success_count=1,
        avg_score=score
    )
    await database.save_akasha_template(template.model_dump())
    return template


async def update_template_score(template_id: str, new_score: float) -> None:
    """Update running average score when an existing template succeeds again."""
    # Load existing templates to find the one by id
    all_templates = await database.list_akasha_templates()
    for t in all_templates:
        if t["id"] == template_id:
            count = t["success_count"] + 1
            avg = (t["avg_score"] * t["success_count"] + new_score) / count
            t["success_count"] = count
            t["avg_score"] = avg
            await database.save_akasha_template(t)
            break


async def get_best_template(category: str) -> Optional[AkashaTemplate]:
    """Retrieve the highest-scoring template for a given category."""
    templates = await database.list_akasha_templates(category=category)
    if not templates:
        return None
    best = max(templates, key=lambda t: t["avg_score"])
    return AkashaTemplate(**best)


async def list_templates(category: Optional[str] = None) -> List[AkashaTemplate]:
    """Return all known templates, optionally filtered by category."""
    rows = await database.list_akasha_templates(category=category)
    return [AkashaTemplate(**r) for r in rows]


# ─── Seed: Built-in starter templates ──────────────────────────────────────────

STARTER_TEMPLATES: List[Dict[str, Any]] = [
    {
        "name": "Government Education Grants",
        "category": "education",
        "goal_template": (
            "Search grants.gov for education grants. Filter by: {focus_areas}. "
            "Location: {location}. Return top 10 grants as JSON with title, funder, "
            "amount, deadline, url, description."
        ),
        "avg_score": 8.5,
        "success_count": 12
    },
    {
        "name": "Foundation Healthcare Grants",
        "category": "healthcare",
        "goal_template": (
            "Search the Robert Wood Johnson Foundation, Bill & Melinda Gates Foundation, "
            "and CDC foundation grants portal. Query: {focus_areas} in {location}. "
            "Return structured JSON with grant name, funder, award range, deadline, URL."
        ),
        "avg_score": 7.9,
        "success_count": 8
    },
    {
        "name": "STEM Nonprofit Grants",
        "category": "stem",
        "goal_template": (
            "Search NSF.gov, NIH grants, and STEM.org foundation database for "
            "{focus_areas} grants. Organization type: nonprofit. "
            "Budget range: {budget}. Location: {location}. "
            "Return top matches as JSON."
        ),
        "avg_score": 8.1,
        "success_count": 6
    },
    {
        "name": "Small Business & Startup Grants",
        "category": "business",
        "goal_template": (
            "Search SBA.gov SBIR/STTR grants, grants.gov business grants, "
            "and InnoCentive for startup funding. Focus: {focus_areas}. "
            "Return JSON with title, funder, amount, eligibility, deadline, url."
        ),
        "avg_score": 7.5,
        "success_count": 4
    }
]


async def seed_starter_templates() -> None:
    """Insert built-in templates if Akasha Ledger is empty."""
    existing = await database.list_akasha_templates()
    if existing:
        return  # Already seeded

    for t in STARTER_TEMPLATES:
        await database.save_akasha_template({
            "id": str(uuid.uuid4()),
            "name": t["name"],
            "goal_template": t["goal_template"],
            "category": t["category"],
            "success_count": t["success_count"],
            "avg_score": t["avg_score"],
            "last_used": None
        })
    print("[Akasha Ledger] Seeded starter templates")
