"""Main chat handler: text messages → Claude → streaming response."""

from __future__ import annotations

import asyncio
import logging
from typing import List

from aiogram import F, Router
from aiogram.types import Message

from claude_manager import ClaudeManager
from config import Config

logger = logging.getLogger(__name__)
router = Router()

TELEGRAM_MAX_LEN = 4096
EDIT_INTERVAL = 1.5  # seconds between Telegram message edits


def _get_thread_id(message: Message) -> int:
    return message.message_thread_id or message.chat.id


def _split_message(text: str) -> List[str]:
    """Split text into chunks respecting Telegram's 4096 char limit."""
    if len(text) <= TELEGRAM_MAX_LEN:
        return [text]
    parts = []
    while text:
        if len(text) <= TELEGRAM_MAX_LEN:
            parts.append(text)
            break
        # Find a good break point (newline or space)
        cut = text.rfind("\n", 0, TELEGRAM_MAX_LEN)
        if cut == -1 or cut < TELEGRAM_MAX_LEN // 2:
            cut = text.rfind(" ", 0, TELEGRAM_MAX_LEN)
        if cut == -1:
            cut = TELEGRAM_MAX_LEN
        parts.append(text[:cut])
        text = text[cut:].lstrip("\n")
    return parts


def _escape_markdown(text: str) -> str:
    """Minimal escape for Markdown parse mode — only backtick issues."""
    if text.count("`") % 2 != 0:
        text += "`"
    return text


@router.message(F.text & ~F.text.startswith("/"))
async def handle_message(message: Message, config: Config, claude: ClaudeManager) -> None:
    """Handle text messages: send to Claude, stream response back."""
    if message.from_user is None or message.from_user.id != config.allowed_user_id:
        return

    thread_id = _get_thread_id(message)
    user_text = message.text.strip() if message.text else ""
    if not user_text:
        return

    # Send placeholder
    status_msg = await message.reply("_Thinking..._", parse_mode="Markdown")

    last_edit_time = asyncio.get_event_loop().time()
    last_edit_len = 0

    async def stream_callback(current_text: str) -> None:
        nonlocal last_edit_time, last_edit_len
        now = asyncio.get_event_loop().time()

        # Debounce: don't spam Telegram with edits
        if (now - last_edit_time < EDIT_INTERVAL
                and len(current_text) - last_edit_len < 300):
            return

        # Truncate for preview (leave room for "..." suffix)
        preview = current_text[:TELEGRAM_MAX_LEN - 10]
        preview = _escape_markdown(preview)

        try:
            await status_msg.edit_text(preview + "\n\n_..._", parse_mode="Markdown")
            last_edit_time = now
            last_edit_len = len(current_text)
        except Exception:
            # TelegramBadRequest if text unchanged or rate limited
            pass

    # Query Claude — thread_id determines project via DB
    result = await claude.send(
        thread_id=thread_id,
        text=user_text,
        stream_callback=stream_callback,
    )

    # Format final response
    response_text = result.text
    if not result.is_error and result.cost_usd > 0:
        response_text += f"\n\n_${result.cost_usd:.4f}_"

    # Split and send
    parts = _split_message(response_text)
    if not parts:
        parts = ["_No response._"]

    # Edit placeholder with first part
    first_part = _escape_markdown(parts[0])
    try:
        await status_msg.edit_text(first_part, parse_mode="Markdown")
    except Exception:
        # Fallback: send without markdown if parsing fails
        try:
            await status_msg.edit_text(parts[0])
        except Exception:
            logger.exception("Failed to edit status message")

    # Send remaining parts as separate messages
    for part in parts[1:]:
        try:
            await message.reply(
                _escape_markdown(part),
                parse_mode="Markdown",
                message_thread_id=message.message_thread_id,
            )
        except Exception:
            await message.reply(
                part,
                message_thread_id=message.message_thread_id,
            )
