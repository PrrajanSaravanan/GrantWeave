"""
GrantWeave — Weave Mesh: Dynamic Agent Coordination
Cells are individual TinyFish agent runs. Cells can recruit sub-Cells for parallel work.
The Mesh tracks all active tasks and propagates results upstream.
"""

import asyncio
import uuid
from typing import Dict, Any, List, Callable, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum


class CellStatus(str, Enum):
    PENDING  = "pending"
    RUNNING  = "running"
    SUCCESS  = "success"
    FAILED   = "failed"
    MUTATING = "mutating"


@dataclass
class Cell:
    """A single agent execution unit in the Weave Mesh."""
    id: str
    session_id: str
    goal: str
    strategy: str = "primary"
    status: CellStatus = CellStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    streaming_url: Optional[str] = None
    children: List["Cell"] = field(default_factory=list)


class WeaveMesh:
    """
    Manages a pool of concurrent Cell tasks.
    Provides spawn, recruit (sub-task), and gather operations.
    """

    def __init__(self, session_id: str, max_agents: int = 6):
        self.session_id = session_id
        self.max_agents = max_agents
        self._cells: Dict[str, Cell] = {}
        self._semaphore = asyncio.Semaphore(max_agents)
        self._event_callbacks: List[Callable] = []

    def on_event(self, callback: Callable) -> None:
        """Register a callback to receive Cell lifecycle events."""
        self._event_callbacks.append(callback)

    async def _emit(self, event_type: str, cell: Cell, extra: Dict = {}) -> None:
        for cb in self._event_callbacks:
            await cb(event_type, cell, extra)

    def spawn_cell(self, goal: str, strategy: str = "primary") -> Cell:
        """Create a new Cell (not yet running)."""
        cell = Cell(
            id=str(uuid.uuid4()),
            session_id=self.session_id,
            goal=goal,
            strategy=strategy,
            status=CellStatus.PENDING
        )
        self._cells[cell.id] = cell
        return cell

    async def run_cell(
        self,
        cell: Cell,
        runner: Callable  # async generator that yields TFEvents
    ) -> Cell:
        """Execute a Cell with the given runner coroutine."""
        async with self._semaphore:
            cell.status = CellStatus.RUNNING
            await self._emit("CELL_STARTED", cell)

            try:
                async for event in runner(cell.goal):
                    if event.kind == "STREAMING_URL" and event.streaming_url:
                        cell.streaming_url = event.streaming_url
                        await self._emit("STREAMING_URL", cell, {"url": event.streaming_url})
                    elif event.kind == "COMPLETE":
                        cell.result = event.result_json or {}
                        cell.status = CellStatus.SUCCESS
                        await self._emit("CELL_COMPLETE", cell)
                    elif event.kind == "ERROR":
                        cell.error = event.error
                        cell.status = CellStatus.FAILED
                        await self._emit("CELL_FAILED", cell, {"error": event.error})
            except Exception as exc:
                cell.error = str(exc)
                cell.status = CellStatus.FAILED
                await self._emit("CELL_FAILED", cell, {"error": str(exc)})

        return cell

    async def recruit(
        self,
        parent_cell: Cell,
        goals: List[str],
        runner: Callable
    ) -> List[Cell]:
        """
        Spawn sub-Cells for parallel execution.
        Sub-Cells are linked to the parent cell.
        """
        sub_cells = []
        tasks = []
        for goal in goals:
            child = self.spawn_cell(goal, strategy="recruited")
            parent_cell.children.append(child)
            sub_cells.append(child)
            tasks.append(self.run_cell(child, runner))

        await asyncio.gather(*tasks, return_exceptions=True)
        return sub_cells

    async def run_all(self, cells: List[Cell], runner: Callable) -> List[Cell]:
        """Run a list of cells concurrently (respecting semaphore limit)."""
        tasks = [self.run_cell(cell, runner) for cell in cells]
        await asyncio.gather(*tasks, return_exceptions=True)
        return cells

    def get_streaming_urls(self) -> List[str]:
        return [c.streaming_url for c in self._cells.values() if c.streaming_url]

    def get_all_results(self) -> List[Dict[str, Any]]:
        results = []
        for cell in self._cells.values():
            if cell.result:
                results.append(cell.result)
        return results

    def summary(self) -> Dict[str, Any]:
        cells = list(self._cells.values())
        return {
            "total": len(cells),
            "running": sum(1 for c in cells if c.status == CellStatus.RUNNING),
            "success": sum(1 for c in cells if c.status == CellStatus.SUCCESS),
            "failed": sum(1 for c in cells if c.status == CellStatus.FAILED),
        }
