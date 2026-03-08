"""
GrantWeave — Temporal Fabric
Session checkpoint and recovery system.
Saves full session state to SQLite so interrupted hunts can be resumed.
"""

import uuid
import json
from typing import Optional, Dict, Any
import database


async def save_checkpoint(session_id: str, state: Dict[str, Any]) -> str:
    """
    Snapshot current session state to the checkpoints table.
    Returns the checkpoint id.
    """
    checkpoint_id = str(uuid.uuid4())
    await database.save_checkpoint({
        "id": checkpoint_id,
        "session_id": session_id,
        "state": state
    })
    print(f"[Temporal Fabric] Checkpoint saved for session {session_id}")
    return checkpoint_id


async def load_checkpoint(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Load the most recent checkpoint for a session.
    Returns None if no checkpoint exists.
    """
    checkpoint = await database.load_checkpoint(session_id)
    if checkpoint:
        print(f"[Temporal Fabric] Loaded checkpoint for session {session_id}")
        return checkpoint["state"]
    return None


async def build_state_snapshot(
    session_id: str,
    org_profile: Dict[str, Any],
    command: str,
    grants_so_far: list,
    streaming_urls: list,
    evo_attempts: int,
    phase: str
) -> Dict[str, Any]:
    """
    Build a serializable state dict for checkpointing.
    """
    return {
        "session_id": session_id,
        "org_profile": org_profile,
        "command": command,
        "grants_so_far": grants_so_far,
        "streaming_urls": streaming_urls,
        "evo_attempts": evo_attempts,
        "phase": phase
    }
