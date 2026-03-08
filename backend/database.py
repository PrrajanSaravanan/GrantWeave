"""
GrantWeave — Database Layer
SQLite via aiosqlite. Manages all persistent state for the AetherForge kernel.

Tables:
  org_profiles      — Organization profiles (onboarding data)
  sessions          — Grant hunting sessions
  grant_results     — Individual grant matches
  evo_log           — EvoForge mutation history
  checkpoints       — Temporal Fabric session snapshots
  akasha_templates  — Akasha Ledger: successful goal templates
  wrapped_reports   — GrantWeave Wrapped weekly reports
"""

import asyncio
import aiosqlite
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "aetherforge.db")


async def init_db() -> None:
    """Create all tables if they do not exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS org_profiles (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                mission     TEXT,
                ein         TEXT,
                focus_areas TEXT,   -- JSON array of strings
                location    TEXT,
                budget      REAL,
                founded     INTEGER,
                website     TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id           TEXT PRIMARY KEY,
                org_id       TEXT REFERENCES org_profiles(id),
                command      TEXT NOT NULL,
                status       TEXT DEFAULT 'pending',
                started_at   TEXT DEFAULT (datetime('now')),
                completed_at TEXT,
                grants_found INTEGER DEFAULT 0,
                share_token  TEXT UNIQUE
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS grant_results (
                id            TEXT PRIMARY KEY,
                session_id    TEXT REFERENCES sessions(id),
                title         TEXT NOT NULL,
                funder        TEXT,
                amount        TEXT,
                deadline      TEXT,
                url           TEXT,
                category      TEXT,
                match_score   REAL,
                description   TEXT,
                requirements  TEXT,
                status        TEXT DEFAULT 'found',
                created_at    TEXT DEFAULT (datetime('now'))
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS evo_log (
                id             TEXT PRIMARY KEY,
                session_id     TEXT REFERENCES sessions(id),
                attempt        INTEGER,
                original_goal  TEXT,
                mutated_goal   TEXT,
                strategy       TEXT,
                result         TEXT,  -- 'success' | 'failure' | 'pending'
                score          REAL,
                created_at     TEXT DEFAULT (datetime('now'))
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id         TEXT PRIMARY KEY,
                session_id TEXT REFERENCES sessions(id),
                state_json TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS akasha_templates (
                id           TEXT PRIMARY KEY,
                name         TEXT NOT NULL,
                goal_template TEXT NOT NULL,
                category     TEXT,
                success_count INTEGER DEFAULT 0,
                avg_score    REAL DEFAULT 0.0,
                last_used    TEXT,
                created_at   TEXT DEFAULT (datetime('now'))
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS wrapped_reports (
                id            TEXT PRIMARY KEY,
                org_id        TEXT REFERENCES org_profiles(id),
                week_of       TEXT NOT NULL,
                sessions_run  INTEGER DEFAULT 0,
                grants_found  INTEGER DEFAULT 0,
                best_match    TEXT,
                mutations_run INTEGER DEFAULT 0,
                data_json     TEXT,
                created_at    TEXT DEFAULT (datetime('now'))
            )
        """)

        await db.commit()
    print(f"[DB] Initialized database at {DB_PATH}")


# ─── Org Profiles ─────────────────────────────────────────────────────────────

async def save_org_profile(profile: Dict[str, Any]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO org_profiles
                (id, name, mission, ein, focus_areas, location, budget, founded, website)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            profile["id"], profile["name"], profile.get("mission"),
            profile.get("ein"), json.dumps(profile.get("focus_areas", [])),
            profile.get("location"), profile.get("budget"),
            profile.get("founded"), profile.get("website")
        ))
        await db.commit()


async def get_org_profile(org_id: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM org_profiles WHERE id=?", (org_id,)) as cur:
            row = await cur.fetchone()
            if row:
                d = dict(row)
                d["focus_areas"] = json.loads(d.get("focus_areas") or "[]")
                return d
    return None


async def list_org_profiles() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM org_profiles ORDER BY created_at DESC") as cur:
            rows = await cur.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d["focus_areas"] = json.loads(d.get("focus_areas") or "[]")
                result.append(d)
            return result


# ─── Sessions ─────────────────────────────────────────────────────────────────

async def create_session(session: Dict[str, Any]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO sessions (id, org_id, command, status, share_token)
            VALUES (?, ?, ?, ?, ?)
        """, (session["id"], session.get("org_id"), session["command"],
              session.get("status", "running"), session.get("share_token")))
        await db.commit()


async def update_session(session_id: str, updates: Dict[str, Any]) -> None:
    sets = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [session_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE sessions SET {sets} WHERE id=?", vals)
        await db.commit()


async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_session_by_token(token: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM sessions WHERE share_token=?", (token,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def list_sessions(limit: int = 20) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?", (limit,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# ─── Grant Results ─────────────────────────────────────────────────────────────

async def save_grant(grant: Dict[str, Any]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO grant_results
                (id, session_id, title, funder, amount, deadline, url,
                 category, match_score, description, requirements, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            grant["id"], grant["session_id"], grant["title"], grant.get("funder"),
            grant.get("amount"), grant.get("deadline"), grant.get("url"),
            grant.get("category"), grant.get("match_score", 0.0),
            grant.get("description"), grant.get("requirements"), grant.get("status", "found")
        ))
        await db.commit()


async def list_grants(session_id: Optional[str] = None) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if session_id:
            async with db.execute(
                "SELECT * FROM grant_results WHERE session_id=? ORDER BY match_score DESC",
                (session_id,)
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with db.execute(
                "SELECT * FROM grant_results ORDER BY match_score DESC LIMIT 100"
            ) as cur:
                rows = await cur.fetchall()
        return [dict(r) for r in rows]


# ─── EvoLog ────────────────────────────────────────────────────────────────────

async def save_evo_entry(entry: Dict[str, Any]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO evo_log
                (id, session_id, attempt, original_goal, mutated_goal, strategy, result, score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry["id"], entry["session_id"], entry["attempt"],
            entry["original_goal"], entry["mutated_goal"], entry["strategy"],
            entry.get("result", "pending"), entry.get("score", 0.0)
        ))
        await db.commit()


async def list_evo_log(session_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if session_id:
            async with db.execute(
                "SELECT * FROM evo_log WHERE session_id=? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit)
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with db.execute(
                "SELECT * FROM evo_log ORDER BY created_at DESC LIMIT ?", (limit,)
            ) as cur:
                rows = await cur.fetchall()
        return [dict(r) for r in rows]


# ─── Checkpoints ───────────────────────────────────────────────────────────────

async def save_checkpoint(checkpoint: Dict[str, Any]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO checkpoints (id, session_id, state_json)
            VALUES (?, ?, ?)
        """, (checkpoint["id"], checkpoint["session_id"], json.dumps(checkpoint["state"])))
        await db.commit()


async def load_checkpoint(session_id: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM checkpoints WHERE session_id=? ORDER BY created_at DESC LIMIT 1",
            (session_id,)
        ) as cur:
            row = await cur.fetchone()
            if row:
                d = dict(row)
                d["state"] = json.loads(d["state_json"])
                return d
    return None


# ─── Akasha Ledger ─────────────────────────────────────────────────────────────

async def save_akasha_template(template: Dict[str, Any]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO akasha_templates
                (id, name, goal_template, category, success_count, avg_score, last_used)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            template["id"], template["name"], template["goal_template"],
            template.get("category"), template.get("success_count", 0),
            template.get("avg_score", 0.0), datetime.utcnow().isoformat()
        ))
        await db.commit()


async def list_akasha_templates(category: Optional[str] = None) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if category:
            async with db.execute(
                "SELECT * FROM akasha_templates WHERE category=? ORDER BY avg_score DESC",
                (category,)
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with db.execute(
                "SELECT * FROM akasha_templates ORDER BY avg_score DESC"
            ) as cur:
                rows = await cur.fetchall()
        return [dict(r) for r in rows]


# ─── Wrapped Reports ───────────────────────────────────────────────────────────

async def save_wrapped_report(report: Dict[str, Any]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO wrapped_reports
                (id, org_id, week_of, sessions_run, grants_found, best_match, mutations_run, data_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report["id"], report.get("org_id"), report["week_of"],
            report.get("sessions_run", 0), report.get("grants_found", 0),
            report.get("best_match"), report.get("mutations_run", 0),
            json.dumps(report.get("data", {}))
        ))
        await db.commit()


async def get_wrapped_report(org_id: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM wrapped_reports WHERE org_id=? ORDER BY week_of DESC LIMIT 1",
            (org_id,)
        ) as cur:
            row = await cur.fetchone()
            if row:
                d = dict(row)
                d["data"] = json.loads(d.get("data_json") or "{}")
                return d
    return None
