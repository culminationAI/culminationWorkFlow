"""Agent bot configuration. Loads env vars."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BOT_DIR = Path(__file__).resolve().parent
DB_PATH = BOT_DIR / "agent_bot.db"

# Workspace root defaults to parent of bot/ directory (the workflow root).
# Override with MAIN_DIR env var if needed.
_DEFAULT_MAIN_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_MCP_CONFIG = _DEFAULT_MAIN_DIR / "mcp" / "mcp.json"


@dataclass
class Config:
    telegram_token: str
    allowed_user_id: int
    main_dir: Path  # workspace root
    mcp_config_path: Path
    db_path: Path = DB_PATH
    max_turns: int = 50
    default_model: str = "claude-sonnet-4-6"

    @classmethod
    def from_env(cls) -> Config:
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set")

        user_id_str = os.environ.get("ALLOWED_USER_ID", "")
        if not user_id_str:
            raise ValueError("ALLOWED_USER_ID not set")
        user_id = int(user_id_str)

        # Main workspace directory — defaults to parent of bot/
        main_dir_str = os.environ.get("MAIN_DIR", "")
        main_dir = Path(main_dir_str) if main_dir_str else _DEFAULT_MAIN_DIR
        main_dir = main_dir.resolve()

        # MCP config path — defaults to {main_dir}/mcp/mcp.json
        mcp_path_str = os.environ.get("MCP_CONFIG_PATH", "")
        mcp_config = Path(mcp_path_str) if mcp_path_str else (main_dir / "mcp" / "mcp.json")

        return cls(
            telegram_token=token,
            allowed_user_id=user_id,
            main_dir=main_dir,
            mcp_config_path=mcp_config,
        )
