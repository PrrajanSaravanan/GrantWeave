"""
GrantWeave — WebSocket Manager
Real-time team handoff: broadcasts live session state to all connected peers.
Used by the Team Handoff feature to sync multiple browser tabs.
"""

import json
import asyncio
from typing import Dict, List
from fastapi import WebSocket


class WebSocketManager:
    """Manages WebSocket connections grouped by session_id."""

    def __init__(self):
        # Maps session_id → list of active WebSocket connections
        self._connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if session_id not in self._connections:
            self._connections[session_id] = []
        self._connections[session_id].append(websocket)
        print(f"[WS] Client connected to session {session_id}  "
              f"({len(self._connections[session_id])} total)")

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        if session_id in self._connections:
            try:
                self._connections[session_id].remove(websocket)
            except ValueError:
                pass
            if not self._connections[session_id]:
                del self._connections[session_id]
        print(f"[WS] Client disconnected from session {session_id}")

    async def broadcast(self, session_id: str, data: dict) -> None:
        """Send data to all peers watching this session."""
        if session_id not in self._connections:
            return
        dead = []
        for ws in self._connections[session_id]:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(session_id, ws)

    def peer_count(self, session_id: str) -> int:
        return len(self._connections.get(session_id, []))

    def all_sessions(self) -> List[str]:
        return list(self._connections.keys())


# Singleton used across the FastAPI app
ws_manager = WebSocketManager()
