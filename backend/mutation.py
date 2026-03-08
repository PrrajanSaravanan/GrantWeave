"""
GrantWeave — EvoForge: Automatic Mutation Engine
AetherForge kernel component that spawns improved goal variants on failure
and selects the best result by scoring strategy.

On any agent failure:
  1. Generate 3–4 mutated goal variants using different strategies
  2. Run all variants concurrently
  3. Score results by: JSON validity + grant count + match quality
  4. Persist winning variant to Akasha Ledger for future reuse
"""

import asyncio
import uuid
import json
from typing import List, Tuple, Optional, Dict, Any
from models import TFEvent, EvoLogEntry

# ─── Mutation Strategies ───────────────────────────────────────────────────────

MUTATION_STRATEGIES = [
    {
        "name": "strict_schema",
        "description": "Add strict JSON schema with exact field names",
        "suffix": (
            " CRITICAL: output ONLY valid JSON, no extra text. "
            "Schema: {\"grants\":[{\"title\":string,\"funder\":string,"
            "\"amount\":string,\"deadline\":string,\"url\":string,"
            "\"description\":string}]}"
        )
    },
    {
        "name": "pagination_aware",
        "description": "Handle multi-page results and pagination",
        "suffix": (
            " Navigate through ALL pages of results (click 'Next', 'Load More', etc). "
            "Collect grants from at least 3 pages before stopping. "
            "Return aggregated results as JSON."
        )
    },
    {
        "name": "popup_handler",
        "description": "Dismiss popups and cookie banners before extracting",
        "suffix": (
            " Before searching: close any cookie banners, newsletter popups, "
            "or GDPR consent dialogs by clicking Accept/Close/Dismiss. "
            "Then proceed with the search and return JSON results."
        )
    },
    {
        "name": "alternative_source",
        "description": "Try alternative grant databases if primary fails",
        "suffix": (
            " If grants.gov is unavailable, try these alternatives in order: "
            "sam.gov, usaspending.gov, candid.org/grants, grantspace.org. "
            "Return results as JSON from whichever source responds."
        )
    },
    {
        "name": "simplified_search",
        "description": "Use simpler search terms to avoid no-results",
        "suffix": (
            " Use only the most essential keywords from the search query. "
            "Broaden the search if the first attempt returns 0 results. "
            "Try synonyms (grant/funding/award/subsidy). Return JSON."
        )
    }
]


def mutate_goal(
    original_goal: str,
    failure_reason: str,
    attempt: int,
    num_variants: int = 4
) -> List[Tuple[str, str]]:
    """
    Generate `num_variants` mutated goal strings based on failure context.
    Returns list of (mutated_goal, strategy_name) tuples.
    
    The strategy selection is deterministic per attempt so reruns are consistent.
    """
    # Pick N strategies, rotating based on attempt number for variety
    selected = []
    for i in range(num_variants):
        idx = (attempt + i) % len(MUTATION_STRATEGIES)
        strategy = MUTATION_STRATEGIES[idx]
        mutated = original_goal + strategy["suffix"]
        # Inject failure context for context-aware mutations
        if "CAPTCHA" in failure_reason:
            mutated = (
                "Use human-like behavior: slow mouse movements, random delays. "
                + mutated
            )
        elif "LOGIN" in failure_reason:
            mutated = mutated + " If login is required, use the guest/public access path instead."
        selected.append((mutated, strategy["name"]))
    return selected


def score_result(result: Optional[Dict[str, Any]], tf_event: Optional[TFEvent]) -> float:
    """
    Score a TinyFish COMPLETE result.
    Higher = better.

    Scoring factors:
    - JSON parseable: +2
    - Has 'grants' key: +2
    - Number of grants found (capped at 10): +grants*0.5
    - Has URLs for each grant: +0.2 per grant
    - TF event was COMPLETE (not ERROR): +1
    """
    score = 0.0

    if tf_event and tf_event.kind == "COMPLETE":
        score += 1.0

    if result is None:
        return score

    score += 2.0  # JSON parseable

    grants = result.get("grants", [])
    if isinstance(grants, list):
        score += 2.0  # has grants key
        score += min(len(grants), 10) * 0.5
        for g in grants:
            if isinstance(g, dict) and g.get("url"):
                score += 0.2

    return round(score, 2)


def select_best_result(
    results: List[Tuple[float, Dict[str, Any], str]]
) -> Tuple[float, Dict[str, Any], str]:
    """
    Given a list of (score, result_data, strategy_name) tuples,
    return the one with the highest score.
    """
    return max(results, key=lambda x: x[0])


def build_evo_entry(
    session_id: str,
    attempt: int,
    original_goal: str,
    mutated_goal: str,
    strategy: str,
    result: str = "pending",
    score: float = 0.0
) -> EvoLogEntry:
    """Create an EvoLogEntry for persistence."""
    return EvoLogEntry(
        id=str(uuid.uuid4()),
        session_id=session_id,
        attempt=attempt,
        original_goal=original_goal,
        mutated_goal=mutated_goal,
        strategy=strategy,
        result=result,
        score=score
    )
