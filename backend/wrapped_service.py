"""
GrantWeave — Wrapped Service
Generates the weekly "GrantWeave Wrapped" report — Spotify-style metrics
summarizing an org's grant hunting activity for the past 7 days.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import database
from models import WrappedReport


async def generate_wrapped(org_id: str) -> WrappedReport:
    """
    Aggregate last 7 days of activity for an org and build the Wrapped report.
    """
    week_start = (datetime.utcnow() - timedelta(days=7)).date().isoformat()

    # All sessions for this org
    all_sessions = await database.list_sessions(limit=200)
    org_sessions = [s for s in all_sessions if s.get("org_id") == org_id]
    recent_sessions = [
        s for s in org_sessions if (s.get("started_at") or "") >= week_start
    ]

    sessions_run = len(recent_sessions)
    grants_found = sum(s.get("grants_found", 0) for s in recent_sessions)

    # EvoLog stats
    all_evo = await database.list_evo_log(limit=500)
    recent_evo = [
        e for e in all_evo
        if any(e.get("session_id") == s["id"] for s in recent_sessions)
    ]
    mutations_run = len(recent_evo)
    successful_mutations = [e for e in recent_evo if e.get("result") == "success"]

    # Top grant
    all_grants: List[Dict[str, Any]] = []
    for s in recent_sessions:
        grants = await database.list_grants(session_id=s["id"])
        all_grants.extend(grants)
    all_grants.sort(key=lambda g: g.get("match_score", 0), reverse=True)
    best_match = all_grants[0]["title"] if all_grants else None

    # Category breakdown
    category_counts: Dict[str, int] = {}
    for g in all_grants:
        cat = g.get("category", "Other") or "Other"
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Fun facts
    fun_facts = []
    if mutations_run > 0:
        success_rate = (len(successful_mutations) / mutations_run * 100)
        fun_facts.append(f"EvoForge ran {mutations_run} mutations with {success_rate:.0f}% success rate")
    if grants_found > 0:
        fun_facts.append(f"You discovered {grants_found} grant opportunities this week!")
    if sessions_run > 0:
        fun_facts.append(f"Deployed agents across {sessions_run} hunt sessions")

    report_data = {
        "recent_sessions": [s["id"] for s in recent_sessions],
        "category_breakdown": category_counts,
        "top_grants": [
            {"title": g["title"], "funder": g.get("funder"), "amount": g.get("amount")}
            for g in all_grants[:5]
        ],
        "mutations_by_strategy": _count_strategies(recent_evo),
        "fun_facts": fun_facts,
        "portals_scanned": sessions_run * 6,  # 6 portals per session
        "timeline": [
            {"date": s.get("started_at", "")[:10], "grants": s.get("grants_found", 0)}
            for s in recent_sessions
        ]
    }

    report = WrappedReport(
        id=str(uuid.uuid4()),
        org_id=org_id,
        week_of=week_start,
        sessions_run=sessions_run,
        grants_found=grants_found,
        best_match=best_match,
        mutations_run=mutations_run,
        data=report_data
    )

    await database.save_wrapped_report({
        **report.model_dump(),
        "data": report_data
    })

    return report


def _count_strategies(evo_entries: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for e in evo_entries:
        s = e.get("strategy", "unknown")
        counts[s] = counts.get(s, 0) + 1
    return counts
