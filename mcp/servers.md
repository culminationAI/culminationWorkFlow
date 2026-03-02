# MCP-серверы проекта

Конфигурация: `mcp/mcp.json`

## Подключённые серверы

### Context7
- **Пакет:** `@upstash/context7-mcp`
- **Назначение:** Поиск актуальной документации и примеров кода по библиотекам/фреймворкам
- **Инструменты:**
  - `resolve-library-id` — найти ID библиотеки
  - `query-docs` — запросить документацию

### Filesystem
- **Пакет:** `@modelcontextprotocol/server-filesystem`
- **Назначение:** Файловые операции в рабочей директории (`main/`)

### Neo4j
- **Пакет:** `mcp-neo4j-cypher` (uvx, Python)
- **Назначение:** Прямой доступ к графовой БД — Cypher-запросы, схема, индексы
- **Env:** `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`
- **Статус:** Активируется при запуске Neo4j-контейнера (порт 7687)
- **Кто использует:** data-architect (проектирование), engineer (реализация)

### Qdrant
- **Пакет:** `mcp-server-qdrant` (uvx, Python)
- **Назначение:** Семантическое хранилище — store/find эмбеддингов, отладка векторного поиска
- **Env:** `QDRANT_URL`, `COLLECTION_NAME`, `EMBEDDING_MODEL`
- **Статус:** Активируется при запуске Qdrant-контейнера (порт 6333)
- **Кто использует:** data-architect (проектирование), engineer (реализация)

### GitHub
- **Пакет:** `@modelcontextprotocol/server-github`
- **Назначение:** PR, issues, code review, поиск по коду — прямо из контекста
- **Env:** `GITHUB_PERSONAL_ACCESS_TOKEN`
- **Статус:** Активируется после создания токена

### Playwright
- **Пакет:** `@playwright/mcp` (официальный, Microsoft)
- **Назначение:** Браузерная автоматизация — скрейпинг источников, тестирование UI

### Semgrep
- **Пакет:** `semgrep-mcp` (uvx, Python)
- **Назначение:** Статический анализ безопасности кода — OWASP, уязвимости, секреты

### YouTube Transcript
- **Пакет:** `@kimtaeyoon83/mcp-server-youtube-transcript`
- **Назначение:** Извлечение транскриптов YouTube-видео — субтитры, временные метки
- **Инструменты:**
  - `get_transcript` — извлечь транскрипт видео (url, lang, include_timestamps)
- **Кто использует:** Координатор, исследовательские агенты (парсинг подкастов/лекций)

## Требования

- **Node.js** — для npx-серверов (Context7, Filesystem, GitHub, Playwright, YouTube Transcript)
- **uv/uvx** — для Python-серверов (Neo4j, Qdrant, Semgrep). Установка: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Docker** — для Neo4j и Qdrant контейнеров
