"""
Agent Bot — Telegram multiplexer to Claude Code via Agent SDK.
Run: python bot.py

Each Telegram thread = remote terminal to a project directory.
Claude Code reads CLAUDE.md from cwd automatically.

Requires:
- Python 3.10+
- Claude Code CLI installed (npm install -g @anthropic-ai/claude-code)
- TELEGRAM_BOT_TOKEN and ALLOWED_USER_ID in env
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

# Unset CLAUDECODE to allow SDK to launch Claude Code subprocess
# (otherwise it thinks we're inside a nested session)
os.environ.pop("CLAUDECODE", None)

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# Load env from secrets/.env
try:
    from dotenv import load_dotenv
    secrets_env = Path(__file__).resolve().parent.parent / "secrets" / ".env"
    if secrets_env.exists():
        load_dotenv(secrets_env)
    else:
        load_dotenv()
except ImportError:
    pass

from config import Config
from db import Database, DEFAULT_PROJECTS
from claude_manager import ClaudeManager
from handlers import setup_routers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def register_default_projects(db: Database, main_dir: Path) -> None:
    """Register default projects in DB. Paths resolved from main_dir."""
    for name, rel_path, model, desc in DEFAULT_PROJECTS:
        abs_path = (main_dir / rel_path).resolve()
        await db.upsert_project(
            name=name,
            path=str(abs_path),
            default_model=model,
            description=desc,
        )
        logger.info("Project registered: %s → %s", name, abs_path)


async def main() -> None:
    logger.info("Starting Agent Bot...")

    try:
        config = Config.from_env()
    except ValueError as e:
        logger.error(f"Config error: {e}")
        sys.exit(1)

    # Init DB
    db = Database(config.db_path)
    await db.init()

    # Register default projects
    await register_default_projects(db, config.main_dir)

    # Init Claude manager
    claude = ClaudeManager(config=config, db=db)

    logger.info(f"Allowed user: {config.allowed_user_id}")
    logger.info(f"Main dir: {config.main_dir}")
    logger.info(f"MCP config: {config.mcp_config_path}")

    bot = Bot(
        token=config.telegram_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Inject dependencies into handlers
    dp["config"] = config
    dp["db"] = db
    dp["claude"] = claude

    # Register routers
    dp.include_router(setup_routers())

    logger.info("Bot started. Press Ctrl+C to stop.")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
