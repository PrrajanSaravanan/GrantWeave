"""
GrantWeave — Orchestrator
Ties together Weave Mesh + EvoForge + Temporal Fabric into a single grant-hunting pipeline.

Flow:
  1. Load (or create) a session
  2. Retrieve best Akasha template for the org's focus areas
  3. Build TinyFish goal string
  4. Spawn WeaveMesh cells for concurrent portal scraping
  5. On cell failure → trigger EvoForge mutation (up to 3 retries)
  6. Checkpoint state after each phase
  7. Persist grants to DB
  8. Broadcast SSE events to the client
"""

import asyncio
import uuid
import json
from typing import AsyncGenerator, Dict, Any, List, Optional
from datetime import datetime

import database
import akasha_ledger
import temporal_fabric
import mutation as evo
from weave_mesh import WeaveMesh, CellStatus
from tinyfish_client import run_sse, build_grant_goal
from models import TFEvent, SSEEvent, EvoLogEntry

# Grant portals to scan in parallel
GRANT_PORTALS = [
    "grants.gov",
    "sam.gov/opportunities",
    "candid.org/grants",
    "cdc.gov/grants",
    "nsf.gov/funding",
    "sba.gov/funding-programs/grants",
]


def _sse(event: str, session_id: str, data: Dict[str, Any] = {}) -> str:
    """Format a server-sent event string."""
    payload = json.dumps({"event": event, "session_id": session_id, **data})
    return f"data: {payload}\n\n"


async def hunt_grants(
    session_id: str,
    org_id: str,
    command: str
) -> AsyncGenerator[str, None]:
    """
    Main SSE generator for the /api/hunt endpoint.
    Yields SSE-formatted strings to the client in real time.
    """

    # ── Phase 0: Setup ─────────────────────────────────────────────────────────
    org = await database.get_org_profile(org_id)
    if not org:
        yield _sse("ERROR", session_id, {"message": f"Org {org_id} not found"})
        return

    yield _sse("STARTED", session_id, {
        "message": f"GrantWeave AetherForge kernel initializing for {org['name']}…",
        "org": org["name"]
    })

    # Check if we can resume from a checkpoint
    checkpoint = await temporal_fabric.load_checkpoint(session_id)
    if checkpoint:
        yield _sse("RESUMED", session_id, {
            "message": "Resuming from checkpoint…",
            "phase": checkpoint.get("phase")
        })

    grants_collected: List[Dict[str, Any]] = checkpoint.get("grants_so_far", []) if checkpoint else []
    streaming_urls: List[str] = checkpoint.get("streaming_urls", []) if checkpoint else []
    evo_attempt_count = checkpoint.get("evo_attempts", 0) if checkpoint else 0

    # ── Phase 1: Build Goal & Mesh ──────────────────────────────────────────────

    # Prefer Akasha-learned template over fresh goal if available
    category = org.get("focus_areas", ["general"])[0] if org.get("focus_areas") else "general"
    best_template = await akasha_ledger.get_best_template(category)

    if best_template:
        goal = best_template.goal_template.format(
            focus_areas=", ".join(org.get("focus_areas", [])),
            location=org.get("location", "United States"),
            budget=f"${org.get('budget', 50000):,.0f}" if org.get("budget") else "any"
        )
        yield _sse("AKASHA_HIT", session_id, {
            "message": f"Using proven Akasha template: {best_template.name}",
            "template": best_template.name
        })
    else:
        goal = build_grant_goal(
            command=command,
            org_name=org["name"],
            focus_areas=org.get("focus_areas", []),
            location=org.get("location", "United States"),
            budget=org.get("budget")
        )

    # ── Phase 2: Spawn Weave Mesh ───────────────────────────────────────────────

    mesh = WeaveMesh(session_id=session_id, max_agents=6)
    evo_log_entries: List[EvoLogEntry] = []

    # Event callback: relay mesh events to SSE stream via a queue
    event_queue: asyncio.Queue = asyncio.Queue()

    async def on_mesh_event(event_type: str, cell, extra: Dict = {}) -> None:
        await event_queue.put((event_type, cell, extra))

    mesh.on_event(on_mesh_event)

    # Spawn one cell per portal for concurrent scanning
    cells = []
    for portal in GRANT_PORTALS[:6]:
        portal_goal = goal + f" Focus on {portal} specifically."
        cell = mesh.spawn_cell(portal_goal, strategy=f"portal:{portal}")
        cells.append(cell)

    yield _sse("SCANNING", session_id, {
        "message": f"Deploying {len(cells)} agents across {len(GRANT_PORTALS)} grant portals…",
        "portals": GRANT_PORTALS[:6]
    })

    # Checkpoint before network calls
    state = await temporal_fabric.build_state_snapshot(
        session_id, org, command, grants_collected, streaming_urls, evo_attempt_count, "scanning"
    )
    await temporal_fabric.save_checkpoint(session_id, state)

    # ── Phase 3: Run Cells + EvoForge Mutation on Failure ──────────────────────

    async def cell_runner_wrapper(cell_goal: str):
        """Async generator wrapping tinyfish run_sse for WeaveMesh."""
        async for event in run_sse(cell_goal):
            yield event

    # Run all cells concurrently in background
    run_task = asyncio.create_task(mesh.run_all(cells, cell_runner_wrapper))

    # Drain event queue while cells run
    while not run_task.done() or not event_queue.empty():
        try:
            event_type, cell, extra = await asyncio.wait_for(event_queue.get(), timeout=0.5)
        except asyncio.TimeoutError:
            continue

        if event_type == "STREAMING_URL":
            url = extra.get("url", "")
            if url and url not in streaming_urls:
                streaming_urls.append(url)
            yield _sse("STREAMING_URL", session_id, {
                "url": url,
                "cell_id": cell.id,
                "portal": cell.strategy
            })

        elif event_type == "CELL_COMPLETE":
            grants = cell.result.get("grants", []) if cell.result else []
            for g in grants:
                grant_id = str(uuid.uuid4())
                grant_row = {
                    "id": grant_id,
                    "session_id": session_id,
                    "title": g.get("title", "Untitled Grant"),
                    "funder": g.get("funder"),
                    "amount": g.get("amount"),
                    "deadline": g.get("deadline"),
                    "url": g.get("url"),
                    "category": g.get("category", category),
                    "match_score": round(len(g.get("description", "")) / 100, 2),
                    "description": g.get("description"),
                    "requirements": g.get("requirements"),
                    "status": "found"
                }
                await database.save_grant(grant_row)
                grants_collected.append(grant_row)
                yield _sse("MATCH_FOUND", session_id, {
                    "grant": grant_row,
                    "total_found": len(grants_collected)
                })

        elif event_type == "CELL_FAILED" and evo_attempt_count < 3:
            # Trigger EvoForge mutation
            evo_attempt_count += 1
            failure_reason = extra.get("error", "UNKNOWN")
            yield _sse("EVO_MUTATION", session_id, {
                "message": f"EvoForge: Generating mutation variants for attempt {evo_attempt_count}…",
                "attempt": evo_attempt_count,
                "reason": failure_reason
            })

            variants = evo.mutate_goal(cell.goal, failure_reason, evo_attempt_count, num_variants=3)

            for mutated_goal, strategy_name in variants:
                evo_entry = evo.build_evo_entry(
                    session_id=session_id,
                    attempt=evo_attempt_count,
                    original_goal=cell.goal,
                    mutated_goal=mutated_goal,
                    strategy=strategy_name,
                    result="pending"
                )
                evo_log_entries.append(evo_entry)
                await database.save_evo_entry(evo_entry.model_dump())

                # Run each mutated variant
                variant_results = []
                async for tf_event in run_sse(mutated_goal):
                    if tf_event.kind == "STREAMING_URL" and tf_event.streaming_url:
                        if tf_event.streaming_url not in streaming_urls:
                            streaming_urls.append(tf_event.streaming_url)
                        yield _sse("STREAMING_URL", session_id, {
                            "url": tf_event.streaming_url,
                            "cell_id": cell.id,
                            "strategy": strategy_name
                        })
                    elif tf_event.kind == "COMPLETE":
                        score = evo.score_result(tf_event.result_json, tf_event)
                        variant_results.append((score, tf_event.result_json or {}, strategy_name))

                        # Update evo log entry with result
                        evo_entry.result = "success" if score > 3 else "failure"
                        evo_entry.score = score
                        await database.save_evo_entry(evo_entry.model_dump())

                        yield _sse("EVO_RESULT", session_id, {
                            "strategy": strategy_name,
                            "score": score,
                            "result": evo_entry.result
                        })
                        break
                    elif tf_event.kind == "ERROR":
                        evo_entry.result = "failure"
                        await database.save_evo_entry(evo_entry.model_dump())
                        break

    await run_task  # Ensure mesh is fully done

    # ── Phase 4: Persist & Save Template ───────────────────────────────────────
    total = len(grants_collected)
    if total > 0:
        # Save winning approach to Akasha Ledger
        await akasha_ledger.save_template(
            name=f"Auto: {command[:60]}",
            goal_template=goal,
            category=category,
            score=min(total, 10) * 0.8
        )

    # Update session record
    await database.update_session(session_id, {
        "status": "completed",
        "completed_at": datetime.utcnow().isoformat(),
        "grants_found": total
    })

    # Final checkpoint
    state = await temporal_fabric.build_state_snapshot(
        session_id, org, command, grants_collected, streaming_urls, evo_attempt_count, "completed"
    )
    await temporal_fabric.save_checkpoint(session_id, state)

    yield _sse("COMPLETE", session_id, {
        "message": f"Hunt complete! Found {total} grants across {len(GRANT_PORTALS)} portals.",
        "grants_found": total,
        "streaming_urls": streaming_urls,
        "evo_attempts": evo_attempt_count,
        "mesh_summary": mesh.summary()
    })
