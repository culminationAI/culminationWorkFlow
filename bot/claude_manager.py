"""Claude Agent SDK manager — session pool, query dispatch, streaming."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
)

from config import Config
from db import Database
from threads import ThreadConfig, resolve_thread_config

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    text: str
    session_id: Optional[str] = None
    cost_usd: float = 0.0
    duration_ms: int = 0
    is_error: bool = False


class ClaudeManager:
    def __init__(self, config: Config, db: Database):
        self.config = config
        self.db = db
        # Per-thread locks to serialize requests within one thread
        self._locks: Dict[int, asyncio.Lock] = {}

    def _get_lock(self, thread_id: int) -> asyncio.Lock:
        if thread_id not in self._locks:
            self._locks[thread_id] = asyncio.Lock()
        return self._locks[thread_id]

    def _build_options(
        self,
        thread_config: ThreadConfig,
        session_id: Optional[str] = None,
    ) -> ClaudeAgentOptions:
        opts: Dict[str, Any] = {
            "cwd": str(thread_config.project_path),
            "mcp_servers": str(self.config.mcp_config_path),
            "permission_mode": "acceptEdits",
            "max_turns": self.config.max_turns,
            "model": thread_config.model,
        }

        # Pathfinder source attribution — appended when thread has a source tag
        if thread_config.source:
            opts["system_prompt"] = {
                "type": "preset",
                "preset": "claude_code",
                "append": (
                    f"You are exploring the \"{thread_config.source}\" project as pathfinder. "
                    f"Tag ALL artifacts and data writes with source: \"{thread_config.source}\". "
                    f"Use --source {thread_config.source} when calling memory scripts."
                ),
            }

        if session_id:
            opts["resume"] = session_id

        return ClaudeAgentOptions(**opts)

    async def send(
        self,
        thread_id: int,
        text: str,
        stream_callback: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> QueryResult:
        """Send a message to Claude and return the result.

        Uses per-thread lock to prevent concurrent requests in the same thread.
        Different threads run in parallel.
        """
        lock = self._get_lock(thread_id)

        async with lock:
            # Resolve thread config (project, cwd, model, source)
            thread_config = await resolve_thread_config(
                thread_id, self.db, self.config.main_dir, self.config.default_model
            )

            # Get or create thread record
            record = await self.db.get_thread(thread_id)
            if record is None:
                await self.db.upsert_thread(thread_id)
                session_id = None
            else:
                session_id = record.session_id

            options = self._build_options(thread_config, session_id)

            # Collect response
            full_text = ""
            tool_names: List[str] = []
            result_session_id: Optional[str] = None
            result_cost: float = 0.0

            try:
                async for message in query(prompt=text, options=options):
                    if isinstance(message, AssistantMessage):
                        for block in getattr(message, "content", []):
                            if isinstance(block, TextBlock):
                                full_text += block.text
                                if stream_callback:
                                    await stream_callback(full_text)
                            elif isinstance(block, ToolUseBlock):
                                name = getattr(block, "name", "unknown")
                                tool_names.append(name)
                                if stream_callback:
                                    status = f"{full_text}\n\n`[{name}]...`"
                                    await stream_callback(status)

                    elif isinstance(message, ResultMessage):
                        result_session_id = getattr(message, "session_id", None)
                        result_cost = getattr(message, "total_cost_usd", 0.0) or 0.0

                # Persist session_id for resume
                if result_session_id:
                    await self.db.update_session_id(thread_id, result_session_id)

                # Log messages
                await self.db.log_message(thread_id, "user", text)
                await self.db.log_message(
                    thread_id, "assistant", full_text, cost=result_cost
                )

                return QueryResult(
                    text=full_text,
                    session_id=result_session_id,
                    cost_usd=result_cost,
                )

            except Exception as e:
                logger.exception(f"Error in thread {thread_id}")
                return QueryResult(
                    text=f"Error: {e}",
                    is_error=True,
                )

    async def reset_thread(self, thread_id: int) -> None:
        """Archive thread and clear session."""
        await self.db.archive_thread(thread_id)
        self._locks.pop(thread_id, None)

    async def new_session(self, thread_id: int) -> None:
        """Clear session_id but keep project binding."""
        await self.db.update_session_id(thread_id, None)
