"""Dynamic thread → project resolution.

Each Telegram thread maps to a project (directory with CLAUDE.md).
No hardcoded thread types — everything is DB-driven.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from db import Database, ThreadRecord, ProjectRecord


@dataclass
class ThreadConfig:
    """Runtime config for a Claude session tied to a Telegram thread."""
    project_name: str       # registered project name, or "temp"
    project_path: Path      # absolute path → used as cwd for Claude
    model: str              # resolved model (override > project default)
    source: Optional[str]   # pathfinder attribution tag


async def resolve_thread_config(
    thread_id: int,
    db: Database,
    main_dir: Path,
    default_model: str = "claude-sonnet-4-6",
) -> ThreadConfig:
    """Resolve thread_id to a ThreadConfig.

    Priority: thread model_override > project default_model > global default.
    Unassigned (temp) threads get cwd = main_dir.
    """
    thread = await db.get_thread(thread_id)

    if thread is None or thread.project_name is None:
        # Temp or unknown thread → use main_dir as cwd
        model = default_model
        if thread and thread.model_override:
            model = thread.model_override
        return ThreadConfig(
            project_name="temp",
            project_path=main_dir,
            model=model,
            source=None,
        )

    # Look up project
    project = await db.get_project(thread.project_name)
    if project is None:
        # Project was deleted but thread still references it
        return ThreadConfig(
            project_name=thread.project_name,
            project_path=main_dir,
            model=thread.model_override or default_model,
            source=thread.source,
        )

    # Resolve model: thread override > project default
    model = thread.model_override or project.default_model

    return ThreadConfig(
        project_name=project.name,
        project_path=Path(project.path),
        model=model,
        source=thread.source,
    )
