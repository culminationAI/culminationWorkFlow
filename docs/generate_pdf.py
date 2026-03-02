"""
generate_pdf.py
Assembles all CulminationAI workflow documentation into a single styled HTML file
ready for browser Print→PDF or Playwright PDF generation.

Usage:
    python3 docs/generate_pdf.py

Output:
    docs/CulminationAI-Workflow-Documentation.html
"""

from __future__ import annotations

import re
import unicodedata
from collections import OrderedDict
from datetime import date
from pathlib import Path

import markdown as md_lib

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

WORKFLOW_ROOT = Path(__file__).resolve().parent.parent  # workflow/
OUTPUT_FILE = WORKFLOW_ROOT / "docs" / "CulminationAI-Workflow-Documentation.html"

# ---------------------------------------------------------------------------
# Chapter manifest
# Each entry: (part_title, chapter_title, file_path_relative_to_WORKFLOW_ROOT)
# None as file_path triggers the generator for that chapter.
# ---------------------------------------------------------------------------

CHAPTERS: list[tuple[str, str, str | None]] = [
    # Part 1: Overview
    ("Overview", "Introduction", "README.md"),

    # Part 2: Configuration
    ("Configuration", "Coordinator Configuration (CLAUDE.md)", "CLAUDE.md"),
    ("Configuration", "User Identity Template", "user-identity.md"),

    # Part 3: Agents
    ("Agents", "Pathfinder — Explorer & Knowledge Manager", ".claude/agents/pathfinder.md"),
    ("Agents", "Protocol Manager — Protocol Lifecycle", ".claude/agents/protocol-manager.md"),
    ("Agents", "Engineer — Code & Infrastructure", ".claude/agents/engineer.md"),
    ("Agents", "LLM Engineer — Prompt Design & Context", ".claude/agents/llm-engineer.md"),

    # Part 4: Core Protocols
    ("Core Protocols", "Initialization (9 Phases)", "protocols/core/initialization.md"),
    ("Core Protocols", "Evolution — Self-Improvement", "protocols/core/evolution.md"),
    ("Core Protocols", "Coordination — Parallel Orchestration", "protocols/core/coordination.md"),
    ("Core Protocols", "Query Optimization", "protocols/core/query-optimization.md"),
    ("Core Protocols", "Dispatcher Reference", "protocols/core/dispatcher.md"),
    ("Core Protocols", "MCP Server Management", "protocols/core/mcp-management.md"),

    # Part 5: Agent Protocols
    ("Agent Protocols", "Agent Creation", "protocols/agents/agent-creation.md"),
    ("Agent Protocols", "Agent Communication", "protocols/agents/agent-communication.md"),
    ("Agent Protocols", "Meta Protocol", "protocols/agents/meta.md"),

    # Part 6: Knowledge Protocols
    ("Knowledge Protocols", "Exploration", "protocols/knowledge/exploration.md"),
    ("Knowledge Protocols", "Memory", "protocols/knowledge/memory.md"),
    ("Knowledge Protocols", "Context Engineering", "protocols/knowledge/context-engineering.md"),

    # Part 7: Quality Protocols
    ("Quality Protocols", "Testing & Benchmarks", "protocols/quality/testing.md"),
    ("Quality Protocols", "Cloning — Safe Evolution", "protocols/quality/cloning.md"),
    ("Quality Protocols", "Security & Logging", "protocols/quality/security-logging.md"),

    # Part 8: Project Protocols
    ("Project Protocols", "Monorepo Orchestration", "protocols/project/monorepo-orchestration.md"),

    # Part 9: MCP Servers
    ("MCP Servers", "Server Reference", "mcp/servers.md"),
    ("MCP Servers", "Configuration Script (mcp_configure.py)", "mcp/mcp_configure.py"),

    # Part 10: Memory Layer
    ("Memory Layer", "Memory Configuration", "memory/CLAUDE.md"),
    ("Memory Layer", "Memory Manager Skill", "memory/SKILL.md"),

    # Part 11: Infrastructure
    ("Infrastructure", "Docker Compose", "infra/docker-compose.yml"),
    ("Infrastructure", "Setup Script", "setup.sh"),
    ("Infrastructure", "Environment Variables", "secrets/.env.template"),

    # Part 12: Telegram Bot
    ("Telegram Bot", "Bot Overview", None),
]

# ---------------------------------------------------------------------------
# Markdown extensions
# ---------------------------------------------------------------------------

_EXTENSIONS_PREFERRED = ["tables", "fenced_code", "toc", "codehilite"]
_EXTENSIONS_FALLBACK = ["tables", "fenced_code", "toc"]


def _build_md_extensions() -> list[str]:
    """Try preferred extensions; gracefully drop codehilite if unavailable."""
    try:
        md_lib.markdown("test", extensions=_EXTENSIONS_PREFERRED)
        return _EXTENSIONS_PREFERRED
    except Exception:
        return _EXTENSIONS_FALLBACK


MD_EXTENSIONS = _build_md_extensions()


def render_markdown(text: str) -> str:
    """Convert markdown text to HTML."""
    return md_lib.markdown(text, extensions=MD_EXTENSIONS)


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

_CODE_SUFFIXES = {".py", ".sh", ".yml", ".yaml", ".template", ".json", ".toml", ".env"}


def read_file(rel_path: str) -> str:
    """Read file relative to WORKFLOW_ROOT. Return placeholder on missing."""
    full_path = WORKFLOW_ROOT / rel_path
    if not full_path.exists():
        return f"> *(File not found: `{rel_path}`)*"
    try:
        return full_path.read_text(encoding="utf-8")
    except Exception as exc:
        return f"> *(Error reading `{rel_path}`: {exc})*"


def is_code_file(rel_path: str) -> bool:
    return Path(rel_path).suffix.lower() in _CODE_SUFFIXES


def wrap_code_block(content: str, rel_path: str) -> str:
    """Wrap raw file content in a fenced markdown code block."""
    # Detect language hint from suffix for syntax highlighting
    suffix_to_lang: dict[str, str] = {
        ".py": "python",
        ".sh": "bash",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".json": "json",
        ".toml": "toml",
        ".template": "bash",
        ".env": "bash",
    }
    lang = suffix_to_lang.get(Path(rel_path).suffix.lower(), "")
    return f"```{lang}\n{content}\n```"


def strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter delimited by leading --- ... --- block."""
    stripped = text.strip()
    if not stripped.startswith("---"):
        return text
    # Find the closing ---
    end = stripped.find("\n---", 3)
    if end == -1:
        return text
    return stripped[end + 4:].lstrip("\n")


# ---------------------------------------------------------------------------
# Bot overview generator
# ---------------------------------------------------------------------------


def generate_bot_overview() -> str:
    """Generate functional overview of the Telegram bot from actual source files."""
    return """\
## Architecture

The Telegram bot provides remote access to the Claude Code workflow via Telegram messages.
Each conversation thread maps to a configured project directory on the host machine,
allowing full multi-project management from a single bot instance.

### Components

| File | Responsibility |
|------|---------------|
| `bot/bot.py` | Main entry point, Telegram bot initialization and polling loop |
| `bot/claude_manager.py` | Claude API session management, streaming response handling |
| `bot/threads.py` | Thread-to-project mapping, session persistence across restarts |
| `bot/db.py` | SQLite-based persistence layer for threads and session state |
| `bot/config.py` | Configuration loader (bot token, model, project paths) |
| `bot/handlers/commands.py` | Command handlers: `/start`, `/project`, `/model` |
| `bot/handlers/chat.py` | Message handlers with streaming markdown formatting |

### Features

- Each Telegram thread maps to a project directory
- Streaming responses with live-updated formatted markdown
- Per-thread model switching (Opus / Sonnet / Haiku)
- Session persistence across bot restarts via SQLite
- Multiple projects managed from a single bot instance
- Graceful error handling with user-visible error messages

### Data Flow

```
User message
    → Telegram API
    → bot.py (polling)
    → handlers/chat.py
    → claude_manager.py  ←→  Claude API (streaming)
    → threads.py (session lookup)
    → Telegram API (streamed reply)
```

### Setup

1. Create a Telegram bot via `@BotFather` and copy the token
2. Add `TELEGRAM_BOT_TOKEN` to `secrets/.env`
3. Install dependencies:
   ```bash
   pip install -r bot/requirements.txt
   ```
4. Run:
   ```bash
   python3 bot/bot.py
   ```

### Configuration

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather |
| `ANTHROPIC_API_KEY` | API key for Claude |
| `DEFAULT_MODEL` | Default Claude model (e.g. `claude-opus-4-6`) |
| `PROJECTS_DIR` | Root directory containing project folders |
"""


# ---------------------------------------------------------------------------
# Slug / TOC helpers
# ---------------------------------------------------------------------------


def slugify(text: str) -> str:
    """Convert a chapter title to a URL-safe anchor slug."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def build_toc(parts: OrderedDict[str, list[tuple[str, str]]]) -> str:
    """Build a nested HTML table of contents."""
    lines: list[str] = ['<nav class="toc">']
    lines.append('<h2>Table of Contents</h2>')
    lines.append('<ol class="toc-parts">')

    for part_title, chapters in parts.items():
        part_slug = slugify(part_title)
        lines.append(f'<li class="toc-part">')
        lines.append(f'<a href="#{part_slug}" class="toc-part-link">{part_title}</a>')
        lines.append('<ol class="toc-chapters">')
        for chapter_title, _html in chapters:
            chapter_slug = slugify(chapter_title)
            lines.append(
                f'<li><a href="#{chapter_slug}">{chapter_title}</a></li>'
            )
        lines.append("</ol>")
        lines.append("</li>")

    lines.append("</ol>")
    lines.append("</nav>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

CSS = """
/* =========================================================
   CulminationAI Workflow Documentation — Print Stylesheet
   Optimised for A4 / browser Print→PDF
   ========================================================= */

/* --- Page Setup --- */
@page {
    size: A4;
    margin: 2cm 2.5cm 2.5cm 2.5cm;
    @bottom-center {
        content: counter(page);
        font-family: 'Georgia', serif;
        font-size: 9pt;
        color: #6b7280;
    }
    @bottom-left {
        content: "CulminationAI Workflow";
        font-family: 'Georgia', serif;
        font-size: 9pt;
        color: #9ca3af;
    }
}

@page :first {
    @bottom-center { content: ""; }
    @bottom-left   { content: ""; }
}

/* --- Reset & Base --- */
*, *::before, *::after {
    box-sizing: border-box;
}

html {
    font-size: 11pt;
}

body {
    font-family: 'Georgia', 'Times New Roman', Times, serif;
    font-size: 11pt;
    line-height: 1.7;
    color: #1f2937;
    background: #ffffff;
    margin: 0;
    padding: 0;
    counter-reset: page;
}

/* --- Cover Page --- */
.cover {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    text-align: center;
    page-break-after: always;
    padding: 4cm 2cm;
    background: linear-gradient(160deg, #0f1f3d 0%, #1a365d 60%, #2d4a7a 100%);
    color: #ffffff;
}

.cover-logo {
    font-size: 14pt;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: #93c5fd;
    margin-bottom: 2cm;
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-weight: 300;
}

.cover-title {
    font-size: 32pt;
    font-weight: 700;
    color: #ffffff;
    margin: 0 0 0.4cm 0;
    line-height: 1.15;
    letter-spacing: -0.01em;
}

.cover-subtitle {
    font-size: 14pt;
    color: #bfdbfe;
    margin: 0 0 2cm 0;
    font-weight: 400;
    font-style: italic;
    max-width: 15cm;
}

.cover-meta {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 10pt;
    color: #93c5fd;
    border-top: 1px solid rgba(147, 197, 253, 0.3);
    padding-top: 0.6cm;
    margin-top: 1cm;
    letter-spacing: 0.05em;
}

.cover-meta span {
    display: inline-block;
    margin: 0 0.5cm;
}

/* --- Table of Contents --- */
.toc {
    page-break-after: always;
    padding: 1cm 0 2cm 0;
}

.toc h2 {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 18pt;
    color: #1a365d;
    border-bottom: 3px solid #1a365d;
    padding-bottom: 0.3cm;
    margin-bottom: 0.8cm;
    letter-spacing: -0.01em;
}

.toc-parts {
    list-style: none;
    padding: 0;
    margin: 0;
    counter-reset: toc-part;
}

.toc-part {
    margin-bottom: 0.5cm;
    counter-increment: toc-part;
}

.toc-part-link {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 12pt;
    font-weight: 700;
    color: #1a365d;
    text-decoration: none;
    display: block;
    padding: 0.15cm 0;
    border-bottom: 1px solid #e5e7eb;
}

.toc-part-link:hover { color: #2563eb; }

.toc-chapters {
    list-style: none;
    padding: 0 0 0 1cm;
    margin: 0.2cm 0 0 0;
    counter-reset: toc-chapter;
}

.toc-chapters li {
    counter-increment: toc-chapter;
    padding: 0.05cm 0;
}

.toc-chapters a {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 10pt;
    color: #374151;
    text-decoration: none;
}

.toc-chapters a:hover { color: #2563eb; text-decoration: underline; }

/* --- Part Headers --- */
.part-header {
    page-break-before: always;
    page-break-after: always;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
    text-align: center;
    padding: 2cm;
}

.part-header h1 {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 28pt;
    font-weight: 700;
    color: #1a365d;
    margin: 0;
    padding: 0 0 0.5cm 0;
    border-bottom: 4px solid #1a365d;
    letter-spacing: -0.02em;
    display: inline-block;
}

/* --- Chapters --- */
.chapter {
    page-break-inside: avoid;
    padding: 0 0 1.5cm 0;
    border-bottom: 1px solid #e5e7eb;
    margin-bottom: 1.5cm;
}

.chapter:last-child {
    border-bottom: none;
}

.chapter h2 {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 18pt;
    font-weight: 700;
    color: #1a365d;
    border-bottom: 2px solid #bfdbfe;
    padding-bottom: 0.25cm;
    margin: 0 0 0.6cm 0;
    letter-spacing: -0.01em;
}

/* --- Content Headings --- */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    color: #1a365d;
    line-height: 1.3;
    margin-top: 1em;
    margin-bottom: 0.4em;
}

/* h2 inside chapter content (not the chapter title itself) */
.chapter .chapter-content h1 {
    font-size: 16pt;
    border-bottom: 1px solid #dbeafe;
    padding-bottom: 0.2cm;
    margin-top: 1.2em;
}

.chapter .chapter-content h2 {
    font-size: 14pt;
    color: #1e40af;
    border-bottom: none;
    padding-bottom: 0;
    margin-top: 1em;
}

.chapter .chapter-content h3 {
    font-size: 12pt;
    color: #1e40af;
    font-weight: 600;
}

.chapter .chapter-content h4 {
    font-size: 11pt;
    color: #374151;
    font-weight: 600;
    font-style: italic;
}

/* --- Paragraphs & Lists --- */
p {
    margin: 0 0 0.6em 0;
    text-align: justify;
    hyphens: auto;
}

ul, ol {
    margin: 0.4em 0 0.6em 0;
    padding-left: 1.5em;
}

li {
    margin-bottom: 0.2em;
}

li > ul, li > ol {
    margin-top: 0.2em;
}

/* --- Links --- */
a {
    color: #2563eb;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

/* --- Code --- */
code {
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Courier New', monospace;
    font-size: 0.88em;
    background: #f1f5f9;
    color: #0f172a;
    padding: 0.1em 0.35em;
    border-radius: 3px;
    border: 1px solid #e2e8f0;
    white-space: pre-wrap;
    word-break: break-word;
}

pre {
    background: #f7f8fa;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #1a365d;
    border-radius: 4px;
    padding: 0.7cm 0.8cm;
    overflow-x: auto;
    font-size: 0.85em;
    line-height: 1.5;
    margin: 0.6em 0 0.8em 0;
    page-break-inside: avoid;
}

pre code {
    background: transparent;
    border: none;
    padding: 0;
    font-size: inherit;
    white-space: pre;
    word-break: normal;
    color: #1e293b;
}

/* --- Tables --- */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.6em 0 0.8em 0;
    font-size: 0.93em;
    page-break-inside: avoid;
}

thead {
    background-color: #1a365d;
    color: #ffffff;
}

thead th {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 0.9em;
    font-weight: 600;
    padding: 0.3cm 0.4cm;
    text-align: left;
    letter-spacing: 0.02em;
}

tbody tr:nth-child(even) {
    background-color: #f9fafb;
}

tbody tr:hover {
    background-color: #eff6ff;
}

tbody td {
    padding: 0.2cm 0.4cm;
    border: 1px solid #e5e7eb;
    vertical-align: top;
}

/* --- Blockquotes --- */
blockquote {
    border-left: 4px solid #93c5fd;
    background: #eff6ff;
    margin: 0.6em 0;
    padding: 0.4cm 0.6cm;
    border-radius: 0 4px 4px 0;
    font-style: italic;
    color: #374151;
}

blockquote p {
    margin: 0;
}

/* --- Horizontal Rule --- */
hr {
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 1em 0;
}

/* --- Badges / inline highlights --- */
strong {
    color: #111827;
    font-weight: 700;
}

em {
    color: #374151;
}

/* --- Print overrides --- */
@media print {
    body {
        background: #ffffff;
        font-size: 10.5pt;
    }

    .cover {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
        background: linear-gradient(160deg, #0f1f3d 0%, #1a365d 60%, #2d4a7a 100%) !important;
    }

    .part-header {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }

    thead {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
        background-color: #1a365d !important;
        color: #ffffff !important;
    }

    tbody tr:nth-child(even) {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
        background-color: #f9fafb !important;
    }

    pre {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
        background: #f7f8fa !important;
        border-left-color: #1a365d !important;
    }

    a {
        color: #1a365d;
        text-decoration: none;
    }

    /* Show hrefs after links in print */
    a[href^="http"]:after {
        content: " (" attr(href) ")";
        font-size: 0.75em;
        color: #6b7280;
    }

    .toc {
        page-break-after: always;
    }

    .chapter {
        page-break-inside: auto;
    }

    h2, h3 {
        page-break-after: avoid;
    }

    pre, table, blockquote {
        page-break-inside: avoid;
    }
}

/* --- Screen-only extras --- */
@media screen {
    body {
        max-width: 21cm;
        margin: 0 auto;
        padding: 1cm 2cm;
        background: #f3f4f6;
    }

    .cover,
    .part-header,
    .toc,
    .chapter {
        background: #ffffff;
        border-radius: 6px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.08);
        margin-bottom: 1cm;
        padding: 1.5cm 2cm;
    }

    .cover {
        min-height: auto;
        padding: 3cm 2cm;
    }

    .part-header {
        min-height: auto;
        padding: 2cm;
    }
}
"""

# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="generator" content="CulminationAI generate_pdf.py">
    <title>CulminationAI Workflow Documentation</title>
    <style>
{css}
    </style>
</head>
<body>

<!-- Cover Page -->
<div class="cover">
    <div class="cover-logo">CulminationAI</div>
    <h1 class="cover-title">Workflow Documentation</h1>
    <p class="cover-subtitle">Multi-Agent Orchestration Framework for Claude Code</p>
    <div class="cover-meta">
        <span>Version 1.0</span>
        <span>&nbsp;&bull;&nbsp;</span>
        <span>{date}</span>
        <span>&nbsp;&bull;&nbsp;</span>
        <span>Generated by generate_pdf.py</span>
    </div>
</div>

<!-- Table of Contents -->
{toc}

<!-- Body -->
{body}

</body>
</html>
"""

# ---------------------------------------------------------------------------
# Main assembly
# ---------------------------------------------------------------------------


def main() -> None:
    parts: OrderedDict[str, list[tuple[str, str]]] = OrderedDict()

    for part, chapter, filepath in CHAPTERS:
        # 1. Obtain raw content
        if filepath is None:
            raw_content = generate_bot_overview()
        elif is_code_file(filepath):
            raw_text = read_file(filepath)
            # Don't double-wrap the "file not found" placeholder
            if raw_text.startswith("> *"):
                raw_content = raw_text
            else:
                raw_content = wrap_code_block(raw_text, filepath)
        else:
            raw_content = read_file(filepath)

        # 2. Strip YAML frontmatter from markdown files
        if filepath is not None and filepath.endswith(".md"):
            raw_content = strip_frontmatter(raw_content)

        # 3. Render markdown → HTML
        chapter_html = render_markdown(raw_content)

        parts.setdefault(part, []).append((chapter, chapter_html))

    # Build TOC
    toc_html = build_toc(parts)

    # Build body
    body_parts: list[str] = []
    chapter_num = 0

    for part_title, chapters in parts.items():
        part_slug = slugify(part_title)
        body_parts.append(
            f'<div class="part-header" id="{part_slug}">'
            f"<h1>{part_title}</h1>"
            f"</div>"
        )
        for chapter_title, chapter_html in chapters:
            chapter_num += 1
            slug = slugify(chapter_title)
            body_parts.append(
                f'<div class="chapter" id="{slug}">\n'
                f'<h2>{chapter_num}. {chapter_title}</h2>\n'
                f'<div class="chapter-content">\n'
                f"{chapter_html}\n"
                f"</div>\n"
                f"</div>"
            )

    # Assemble final HTML
    full_html = HTML_TEMPLATE.format(
        css=CSS,
        date=date.today().strftime("%B %d, %Y"),
        toc=toc_html,
        body="\n".join(body_parts),
    )

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE.write_text(full_html, encoding="utf-8")

    print(f"Generated : {OUTPUT_FILE}")
    print(f"Chapters  : {chapter_num}")
    print(f"Parts     : {len(parts)}")
    print(f"Size      : {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    print(f"Extensions: {MD_EXTENSIONS}")


if __name__ == "__main__":
    main()
