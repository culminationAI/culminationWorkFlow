"""SQLite persistence for projects, threads, and message log."""

from __future__ import annotations

import aiosqlite
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional


@dataclass
class ProjectRecord:
    name: str
    path: str
    default_model: str
    description: Optional[str]
    created_at: str


@dataclass
class ThreadRecord:
    thread_id: int
    thread_name: Optional[str]
    project_name: Optional[str]
    status: str  # temp | assigned | archived
    source: Optional[str]  # pathfinder attribution
    session_id: Optional[str]
    model_override: Optional[str]
    created_at: str
    last_active: str
    is_active: int


SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    name            TEXT PRIMARY KEY,
    path            TEXT NOT NULL,
    default_model   TEXT NOT NULL DEFAULT 'claude-sonnet-4-6',
    description     TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS threads (
    thread_id       INTEGER PRIMARY KEY,
    thread_name     TEXT,
    project_name    TEXT REFERENCES projects(name),
    status          TEXT NOT NULL DEFAULT 'temp',
    source          TEXT,
    session_id      TEXT,
    model_override  TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    last_active     TEXT NOT NULL DEFAULT (datetime('now')),
    is_active       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id       INTEGER NOT NULL REFERENCES threads(thread_id),
    role            TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content         TEXT NOT NULL,
    tokens_used     INTEGER DEFAULT 0,
    cost_usd        REAL DEFAULT 0.0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_messages_thread
    ON messages(thread_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_threads_active
    ON threads(is_active, last_active DESC);
"""

# Default projects registered on first startup.
# Only a single generic workspace entry — no project-specific defaults.
DEFAULT_PROJECTS = [
    ("workspace", ".", "claude-sonnet-4-6", "Project workspace (auto-detected)"),
]


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def _get_conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            self._conn = await aiosqlite.connect(self.db_path)
            self._conn.row_factory = aiosqlite.Row
        return self._conn

    # --- Projects ---

    _PROJECT_COLUMNS = ("name", "path", "default_model", "description", "created_at")
    _PROJECT_SELECT = "SELECT " + ", ".join(_PROJECT_COLUMNS) + " FROM projects"

    def _row_to_project(self, row: Any) -> ProjectRecord:
        return ProjectRecord(**{k: row[k] for k in self._PROJECT_COLUMNS})

    async def init(self) -> None:
        conn = await self._get_conn()
        await conn.executescript(SCHEMA)
        # Migration: detect old schema (thread_type, workspace_path) and rebuild
        cursor = await conn.execute("PRAGMA table_info(threads)")
        columns = {row[1] for row in await cursor.fetchall()}
        if "thread_type" in columns or "workspace_path" in columns:
            await self._migrate_from_v1(conn, columns)
        await conn.commit()

    async def _migrate_from_v1(self, conn: aiosqlite.Connection, columns: set) -> None:
        """Migrate from v1 schema (thread_type, workspace_path) to v2 (project_name, status, source)."""
        if "project_name" not in columns:
            await conn.execute("ALTER TABLE threads ADD COLUMN project_name TEXT")
        if "status" not in columns:
            await conn.execute("ALTER TABLE threads ADD COLUMN status TEXT NOT NULL DEFAULT 'temp'")
        if "source" not in columns:
            await conn.execute("ALTER TABLE threads ADD COLUMN source TEXT")
        if "model_override" not in columns:
            await conn.execute("ALTER TABLE threads ADD COLUMN model_override TEXT")
        if "thread_type" in columns:
            await conn.execute(
                "UPDATE threads SET project_name = thread_type WHERE project_name IS NULL"
            )
            await conn.execute(
                "UPDATE threads SET status = 'assigned' WHERE project_name IS NOT NULL"
            )

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def upsert_project(
        self,
        name: str,
        path: str,
        default_model: str = "claude-sonnet-4-6",
        description: Optional[str] = None,
    ) -> None:
        conn = await self._get_conn()
        await conn.execute(
            """INSERT INTO projects (name, path, default_model, description)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET
                   path = excluded.path,
                   default_model = excluded.default_model,
                   description = COALESCE(excluded.description, projects.description)""",
            (name, path, default_model, description),
        )
        await conn.commit()

    async def get_project(self, name: str) -> Optional[ProjectRecord]:
        conn = await self._get_conn()
        cursor = await conn.execute(
            self._PROJECT_SELECT + " WHERE name = ?", (name,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_project(row)

    async def list_projects(self) -> List[ProjectRecord]:
        conn = await self._get_conn()
        cursor = await conn.execute(
            self._PROJECT_SELECT + " ORDER BY name"
        )
        rows = await cursor.fetchall()
        return [self._row_to_project(r) for r in rows]

    # --- Threads ---

    _THREAD_COLUMNS = (
        "thread_id", "thread_name", "project_name", "status", "source",
        "session_id", "model_override", "created_at", "last_active", "is_active",
    )
    _THREAD_SELECT = "SELECT " + ", ".join(_THREAD_COLUMNS) + " FROM threads"

    def _row_to_thread(self, row: Any) -> ThreadRecord:
        return ThreadRecord(**{k: row[k] for k in self._THREAD_COLUMNS})

    async def upsert_thread(
        self,
        thread_id: int,
        name: Optional[str] = None,
    ) -> ThreadRecord:
        """Create a new temp thread or touch existing one."""
        conn = await self._get_conn()
        await conn.execute(
            """INSERT INTO threads (thread_id, thread_name)
               VALUES (?, ?)
               ON CONFLICT(thread_id) DO UPDATE SET last_active = datetime('now')""",
            (thread_id, name),
        )
        await conn.commit()
        return await self.get_thread(thread_id)  # type: ignore[return-value]

    async def assign_thread(
        self,
        thread_id: int,
        project_name: str,
        source: Optional[str] = None,
    ) -> None:
        """Assign thread to a project."""
        conn = await self._get_conn()
        await conn.execute(
            """UPDATE threads
               SET project_name = ?, status = 'assigned', source = ?,
                   session_id = NULL, last_active = datetime('now')
               WHERE thread_id = ?""",
            (project_name, source, thread_id),
        )
        await conn.commit()

    async def unassign_thread(self, thread_id: int) -> None:
        """Unassign thread (back to temp)."""
        conn = await self._get_conn()
        await conn.execute(
            """UPDATE threads
               SET project_name = NULL, status = 'temp', source = NULL,
                   session_id = NULL, last_active = datetime('now')
               WHERE thread_id = ?""",
            (thread_id,),
        )
        await conn.commit()

    async def update_session_id(self, thread_id: int, session_id: Optional[str]) -> None:
        conn = await self._get_conn()
        await conn.execute(
            """UPDATE threads SET session_id = ?, last_active = datetime('now')
               WHERE thread_id = ?""",
            (session_id, thread_id),
        )
        await conn.commit()

    async def set_model_override(self, thread_id: int, model: Optional[str]) -> None:
        conn = await self._get_conn()
        await conn.execute(
            "UPDATE threads SET model_override = ? WHERE thread_id = ?",
            (model, thread_id),
        )
        await conn.commit()

    async def get_thread(self, thread_id: int) -> Optional[ThreadRecord]:
        conn = await self._get_conn()
        cursor = await conn.execute(
            self._THREAD_SELECT + " WHERE thread_id = ?", (thread_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_thread(row)

    async def list_threads(self, active_only: bool = True) -> List[ThreadRecord]:
        conn = await self._get_conn()
        q = self._THREAD_SELECT
        if active_only:
            q += " WHERE is_active = 1"
        q += " ORDER BY last_active DESC"
        cursor = await conn.execute(q)
        rows = await cursor.fetchall()
        return [self._row_to_thread(r) for r in rows]

    async def archive_thread(self, thread_id: int) -> None:
        conn = await self._get_conn()
        await conn.execute(
            "UPDATE threads SET is_active = 0, status = 'archived', session_id = NULL WHERE thread_id = ?",
            (thread_id,),
        )
        await conn.commit()

    # --- Messages ---

    async def log_message(
        self,
        thread_id: int,
        role: str,
        content: str,
        tokens: int = 0,
        cost: float = 0.0,
    ) -> None:
        conn = await self._get_conn()
        await conn.execute(
            """INSERT INTO messages (thread_id, role, content, tokens_used, cost_usd)
               VALUES (?, ?, ?, ?, ?)""",
            (thread_id, role, content, tokens, cost),
        )
        await conn.commit()
