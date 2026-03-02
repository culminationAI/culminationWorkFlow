# MCP-серверы проекта

Конфигурация: `mcp/mcp.json` (активный) · `mcp/mcp-full.json` (все серверы)
Управление: `python3 mcp/mcp_configure.py --help`
Протокол: `protocols/core/mcp-management.md`

## Классификация

### Core (всегда загружены)

| Сервер | Пакет | Назначение | ~Токены |
|--------|-------|------------|---------|
| context7 | @upstash/context7-mcp | Документация библиотек | ~2K |
| filesystem | @modelcontextprotocol/server-filesystem | Файловые операции (directory_tree, move_file) | ~2K |

### Specialized (по необходимости)

| Сервер | Пакет | Назначение | Агенты | ~Токены |
|--------|-------|------------|--------|---------|
| neo4j | mcp-neo4j-cypher | Cypher-запросы, схема графа | data-architect, engineer | ~2K |
| qdrant | mcp-server-qdrant | Векторный поиск, эмбеддинги | data-architect, engineer | ~2K |
| github | @modelcontextprotocol/server-github | PR, issues, code review | engineer, llm-engineer | ~2K |
| playwright | @playwright/mcp | Браузерная автоматизация | engineer | ~2K |
| semgrep | semgrep-mcp | Статический анализ безопасности | engineer | ~2K |
| youtube-transcript | @kimtaeyoon83/mcp-server-youtube-transcript | Транскрипты YouTube | researcher-агенты | ~2K |

## Профили

| Профиль | Серверы | ~Overhead | Когда использовать |
|---------|---------|-----------|-------------------|
| `core` | context7, filesystem | ~4K | Дефолт — большинство сессий |
| `db` | core + neo4j + qdrant | ~8K | Работа с графами/векторами |
| `web` | core + playwright + github | ~8K | Web-разработка, PR review |
| `research` | core + youtube-transcript | ~6K | Исследования с видео |
| `full` | все 8 серверов | ~16K | Кросс-доменная работа, отладка |

### Переключение

```bash
python3 mcp/mcp_configure.py --profile core      # дефолт
python3 mcp/mcp_configure.py --profile db         # + Neo4j + Qdrant
python3 mcp/mcp_configure.py --add github         # добавить один сервер
python3 mcp/mcp_configure.py --status             # текущее состояние
```

**Важно:** после переключения нужен перезапуск Claude Code.

## Env-переменные

| Сервер | Переменные | Загрузка |
|--------|-----------|----------|
| neo4j | NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE | secrets/.env → with-env.sh |
| qdrant | QDRANT_URL | secrets/.env → with-env.sh |
| github | GITHUB_PERSONAL_ACCESS_TOKEN | secrets/.env → with-env.sh |

Серверы context7, filesystem, playwright, semgrep, youtube-transcript не требуют env-переменных.

## Требования

- **Node.js 18+** — npx-серверы (context7, filesystem, github, playwright, youtube-transcript)
- **uv/uvx** — Python-серверы (neo4j, qdrant, semgrep)
- **Docker** — контейнеры Neo4j + Qdrant (только для профилей db и full)
