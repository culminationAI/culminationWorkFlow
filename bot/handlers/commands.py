"""Bot commands: /start, /help, /assign, /unassign, /projects, /new_project,
/threads, /status, /model, /new, /clear."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from claude_manager import ClaudeManager
from config import Config
from db import Database

router = Router()

MODELS = {
    "opus": "claude-opus-4-6",
    "sonnet": "claude-sonnet-4-6",
    "haiku": "claude-haiku-4-5-20251001",
}


def _get_thread_id(message: Message) -> int:
    """Get thread ID. For non-forum chats, use chat_id."""
    return message.message_thread_id or message.chat.id


def _check_user(message: Message, config: Config) -> bool:
    return message.from_user is not None and message.from_user.id == config.allowed_user_id


@router.message(Command("start"))
@router.message(Command("help"))
async def cmd_help(message: Message, config: Config) -> None:
    if not _check_user(message, config):
        return
    await message.reply(
        "*Claude Code Agent Bot*\n\n"
        "Each Telegram thread = remote terminal to a project.\n\n"
        "*Thread management:*\n"
        "/assign <project> — bind thread to project\n"
        "/assign workspace --source X — pathfinder with attribution\n"
        "/unassign — unbind (back to temp)\n"
        "/new — new session (keep binding)\n"
        "/clear — full reset\n\n"
        "*Projects:*\n"
        "/projects — list registered projects\n"
        "/new\\_project <name> — create project dir\n\n"
        "*Info:*\n"
        "/threads — all active threads\n"
        "/status — current thread info\n"
        "/model — switch model (opus/sonnet/haiku)\n"
        "/help — this message",
        parse_mode="Markdown",
    )


@router.message(Command("assign"))
async def cmd_assign(message: Message, config: Config, db: Database, claude: ClaudeManager) -> None:
    """Bind this thread to a project: /assign <project> [--source X]."""
    if not _check_user(message, config):
        return

    thread_id = _get_thread_id(message)
    args = (message.text or "").split()

    if len(args) < 2:
        await message.reply(
            "Usage: `/assign <project>` or `/assign workspace --source myproject`\n"
            "Run `/projects` to see available projects.",
            parse_mode="Markdown",
        )
        return

    project_name = args[1].lower()
    source = None

    # Parse --source flag
    if "--source" in args:
        idx = args.index("--source")
        if idx + 1 < len(args):
            source = args[idx + 1].lower()

    # Check project exists
    project = await db.get_project(project_name)
    if project is None:
        projects = await db.list_projects()
        names = ", ".join(p.name for p in projects)
        await message.reply(
            f"Project `{project_name}` not found.\n"
            f"Available: {names}\n"
            f"Create new: `/new_project {project_name}`",
            parse_mode="Markdown",
        )
        return

    # Ensure thread exists
    record = await db.get_thread(thread_id)
    if record is None:
        await db.upsert_thread(thread_id)

    # Assign
    await db.assign_thread(thread_id, project_name, source=source)

    source_text = f" (source: {source})" if source else ""
    await message.reply(
        f"Thread assigned to *{project_name}*{source_text}\n"
        f"cwd: `{project.path}`",
        parse_mode="Markdown",
    )


@router.message(Command("unassign"))
async def cmd_unassign(message: Message, config: Config, db: Database) -> None:
    """Unbind thread from project (back to temp)."""
    if not _check_user(message, config):
        return
    thread_id = _get_thread_id(message)
    await db.unassign_thread(thread_id)
    await message.reply("Thread unassigned. Back to temp mode.")


@router.message(Command("projects"))
async def cmd_projects(message: Message, config: Config, db: Database) -> None:
    """List all registered projects."""
    if not _check_user(message, config):
        return
    projects = await db.list_projects()
    if not projects:
        await message.reply("No projects registered.")
        return
    lines = ["*Registered projects:*"]
    for p in projects:
        desc = f" — {p.description}" if p.description else ""
        lines.append(f"• `{p.name}` [{p.default_model.split('-')[1]}]{desc}")
        lines.append(f"  `{p.path}`")
    await message.reply("\n".join(lines), parse_mode="Markdown")


@router.message(Command("new_project"))
async def cmd_new_project(message: Message, config: Config, db: Database) -> None:
    """Create a new project directory: /new_project <name> [description]."""
    if not _check_user(message, config):
        return

    args = (message.text or "").split(maxsplit=2)
    if len(args) < 2:
        await message.reply("Usage: `/new_project <name> [description]`", parse_mode="Markdown")
        return

    name = args[1].lower()
    description = args[2] if len(args) > 2 else None

    # Check if already exists
    existing = await db.get_project(name)
    if existing is not None:
        await message.reply(f"Project `{name}` already exists at `{existing.path}`", parse_mode="Markdown")
        return

    # Create directory
    project_dir = config.main_dir / name
    project_dir.mkdir(parents=True, exist_ok=True)

    # Create minimal CLAUDE.md
    claude_md = project_dir / "CLAUDE.md"
    if not claude_md.exists():
        claude_md.write_text(
            f"# {name}\n\n"
            f"{description or 'New project.'}\n",
            encoding="utf-8",
        )

    # Register in DB
    await db.upsert_project(
        name=name,
        path=str(project_dir),
        description=description,
    )

    # Auto-assign current thread
    thread_id = _get_thread_id(message)
    record = await db.get_thread(thread_id)
    if record is None:
        await db.upsert_thread(thread_id)
    await db.assign_thread(thread_id, name)

    await message.reply(
        f"Project *{name}* created at `{project_dir}`\n"
        f"Thread auto-assigned.",
        parse_mode="Markdown",
    )


@router.message(Command("threads"))
async def cmd_threads(message: Message, config: Config, db: Database) -> None:
    """List all active threads with project bindings."""
    if not _check_user(message, config):
        return
    threads = await db.list_threads(active_only=True)
    if not threads:
        await message.reply("No active threads.")
        return
    lines = ["*Active threads:*"]
    for t in threads:
        name = t.thread_name or f"Thread {t.thread_id}"
        project = t.project_name or "temp"
        source_tag = f" (src: {t.source})" if t.source else ""
        model = t.model_override or "default"
        lines.append(f"• {name} → `{project}`{source_tag} [{model}] — {t.last_active}")
    await message.reply("\n".join(lines), parse_mode="Markdown")


@router.message(Command("status"))
async def cmd_status(message: Message, config: Config, db: Database) -> None:
    """Show current thread info."""
    if not _check_user(message, config):
        return
    thread_id = _get_thread_id(message)
    record = await db.get_thread(thread_id)

    if record is None:
        await message.reply("No session for this thread yet. Send a message to start.")
        return

    project = record.project_name or "temp"
    session_display = record.session_id[:16] + "..." if record.session_id else "none"
    model = record.model_override or "project default"
    source_text = f"\n*Source:* {record.source}" if record.source else ""

    # Get project path if assigned
    path_text = ""
    if record.project_name:
        proj = await db.get_project(record.project_name)
        if proj:
            path_text = f"\n*Path:* `{proj.path}`"

    text = (
        f"*Thread:* {thread_id}\n"
        f"*Project:* {project}\n"
        f"*Status:* {record.status}\n"
        f"*Model:* `{model}`"
        f"{source_text}"
        f"{path_text}\n"
        f"*Session:* `{session_display}`\n"
        f"*Last active:* {record.last_active}"
    )
    await message.reply(text, parse_mode="Markdown")


@router.message(Command("model"))
async def cmd_model(message: Message, config: Config, db: Database) -> None:
    """Switch model for this thread: /model sonnet, /model opus, /model haiku."""
    if not _check_user(message, config):
        return
    thread_id = _get_thread_id(message)
    args = (message.text or "").split()

    if len(args) < 2:
        record = await db.get_thread(thread_id)
        current = record.model_override if record and record.model_override else "project default"
        await message.reply(
            f"Current: *{current}*\n\n"
            "Usage: `/model opus` / `/model sonnet` / `/model haiku`",
            parse_mode="Markdown",
        )
        return

    choice = args[1].lower()
    if choice not in MODELS:
        await message.reply(f"Unknown model. Options: {', '.join(MODELS.keys())}")
        return

    await db.set_model_override(thread_id, MODELS[choice])
    await message.reply(f"Model switched to *{choice}* (`{MODELS[choice]}`)", parse_mode="Markdown")


@router.message(Command("new"))
async def cmd_new(message: Message, config: Config, claude: ClaudeManager) -> None:
    """Start new session in this thread. Project binding preserved."""
    if not _check_user(message, config):
        return
    thread_id = _get_thread_id(message)
    await claude.new_session(thread_id)
    await message.reply("New session started. Project binding preserved.")


@router.message(Command("clear"))
async def cmd_clear(message: Message, config: Config, claude: ClaudeManager) -> None:
    """Full reset: archive thread, clear session and binding."""
    if not _check_user(message, config):
        return
    thread_id = _get_thread_id(message)
    await claude.reset_thread(thread_id)
    await message.reply("Thread cleared. Send a message to start fresh.")
