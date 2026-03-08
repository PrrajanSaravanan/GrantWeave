"""
GrantWeave — TinyFish SSE Client
Connects to the TinyFish Web Agent API and streams automation events.

TinyFish Pro tier supports up to 50 concurrent agents.
Endpoint: POST https://agent.tinyfish.ai/v1/automation/run-sse
Auth: X-API-Key header

SSE event types:
  STARTED       — Agent started, contains run_id
  PROGRESS      — Progress update with message
  STREAMING_URL — Live browser view URL (embed in iframe)
  COMPLETE      — Task complete with resultJson payload
  ERROR         — Fatal error
"""

import asyncio
import json
import os
import httpx
from typing import AsyncGenerator, Optional, Dict, Any
from models import TFEvent
from dotenv import load_dotenv

load_dotenv()

TINYFISH_ENDPOINT = os.getenv(
    "TINYFISH_ENDPOINT",
    "https://agent.tinyfish.ai/v1/automation/run-sse"
)
TINYFISH_API_KEY = os.getenv("TINYFISH_API_KEY", "")


def _parse_sse_line(line: str, current_event: Dict[str, Any]) -> None:
    """Parse a single SSE line and mutate current_event dict in place."""
    if line.startswith("event:"):
        current_event["event"] = line[6:].strip()
    elif line.startswith("data:"):
        raw = line[5:].strip()
        try:
            current_event["data"] = json.loads(raw)
        except json.JSONDecodeError:
            current_event["data"] = {"raw": raw}


def _build_tf_event(raw: Dict[str, Any]) -> Optional[TFEvent]:
    """Convert raw parsed SSE dict to TFEvent model."""
    kind = raw.get("event", "").upper()
    data = raw.get("data", {})

    if not kind:
        return None

    return TFEvent(
        kind=kind,
        run_id=data.get("runId") or data.get("run_id"),
        message=data.get("message") or data.get("progress"),
        streaming_url=data.get("streamingUrl") or data.get("streaming_url"),
        result_json=data.get("resultJson") or data.get("result"),
        error=data.get("error") or data.get("message") if kind == "ERROR" else None
    )


async def run_sse(
    goal: str,
    api_key: Optional[str] = None,
    timeout_seconds: float = 120.0
) -> AsyncGenerator[TFEvent, None]:
    """
    Stream automation events from TinyFish for the given goal string.

    The goal must be a detailed JSON-schema-aware instruction so TinyFish
    knows the exact output structure expected:

        "Search grants.gov for education grants. Return JSON:
         {grants: [{title, funder, amount, deadline, url, description}]}"

    Yields TFEvent objects in real time.
    """
    key = api_key or TINYFISH_API_KEY
    if not key:
        # Yield an error event so callers degrade gracefully
        yield TFEvent(
            kind="ERROR",
            error="TINYFISH_API_KEY not set. Add it to your .env file."
        )
        return

    payload = {
        "goal": goal,
        # Tell TinyFish to return structured JSON in its COMPLETE event
        "outputSchema": {
            "type": "object",
            "properties": {
                "grants": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "funder": {"type": "string"},
                            "amount": {"type": "string"},
                            "deadline": {"type": "string"},
                            "url": {"type": "string"},
                            "description": {"type": "string"},
                            "requirements": {"type": "string"},
                            "category": {"type": "string"}
                        }
                    }
                }
            }
        },
        # Error taxonomy TinyFish should classify failures under
        "errorTaxonomy": [
            "CAPTCHA_BLOCKED",
            "LOGIN_REQUIRED",
            "PAGE_NOT_FOUND",
            "TIMEOUT",
            "SCHEMA_MISMATCH",
            "NETWORK_ERROR"
        ]
    }

    headers = {
        "X-API-Key": key,
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            async with client.stream(
                "POST",
                TINYFISH_ENDPOINT,
                json=payload,
                headers=headers
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    yield TFEvent(
                        kind="ERROR",
                        error=f"HTTP {response.status_code}: {body.decode('utf-8', errors='replace')}"
                    )
                    return

                current_event: Dict[str, Any] = {}
                async for raw_line in response.aiter_lines():
                    line = raw_line.strip()

                    if not line:
                        # Empty line signals end of one SSE event block
                        if current_event:
                            tf = _build_tf_event(current_event)
                            if tf:
                                yield tf
                                # Stop after COMPLETE or ERROR
                                if tf.kind in ("COMPLETE", "ERROR"):
                                    return
                        current_event = {}
                        continue

                    _parse_sse_line(line, current_event)

    except httpx.TimeoutException:
        yield TFEvent(kind="ERROR", error="TinyFish request timed out")
    except httpx.RequestError as exc:
        yield TFEvent(kind="ERROR", error=f"Network error: {exc}")


def build_grant_goal(
    command: str,
    org_name: str,
    focus_areas: list,
    location: str,
    budget: Optional[float] = None
) -> str:
    """
    Build a highly-specific TinyFish goal string for grant hunting.
    The more specific the goal, the better the structured output.
    """
    focus_str = ", ".join(focus_areas) if focus_areas else "general nonprofit work"
    budget_str = f"up to ${budget:,.0f}" if budget else "any amount"

    return (
        f"You are a professional grant researcher. Search these grant portals: "
        f"grants.gov, foundationcenter.org (Candid), cdc.gov/grants, "
        f"federalgrants.gov, and any relevant foundation websites. "
        f"User request: {command}. "
        f"Organization: {org_name}. Focus areas: {focus_str}. "
        f"Location: {location or 'United States'}. Budget range: {budget_str}. "
        f"For each grant found, extract: title, funder name, award amount, "
        f"application deadline, direct URL, plain-English description, "
        f"eligibility requirements, and category (federal/state/foundation/corporate). "
        f"Return at least 5 relevant grants ordered by match score (highest first). "
        f"Output MUST be valid JSON with key 'grants' containing an array of objects."
    )
