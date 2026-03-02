# Claude Code — Экосистема скиллов и агентов

> Каталог сообщества: репозитории, скиллы, агенты, команды и бандлы по ролям.
> Источник: ручной аудит топовых репозиториев (февраль 2026).

---

## 1. Репозитории

| Репозиторий | Звёзды | Что внутри | Установка |
|-------------|--------|-----------|-----------|
| [everything-claude-code](https://github.com/affaan-m/everything-claude-code) (affaan-m) | 52.9k | 13 агентов, 50+ скиллов, 33 команды, хуки, 14 MCP конфигов. Победитель хакатона Anthropic | `/plugin marketplace add affaan-m/everything-claude-code` |
| [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills) (sickn33) | 15.9k | 946+ скиллов для Claude Code, Cursor, Gemini CLI. Бандлы по ролям. Веб-каталог | `npx antigravity-awesome-skills` |
| [awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) (hesreallyhim) | — | Курированный список скиллов, хуков, команд, CLI тулов, MCP серверов | Ручное копирование |
| [claude-code-showcase](https://github.com/ChrisWiles/claude-code-showcase) (ChrisWiles) | — | Полная конфигурация проекта: агенты, хуки, команды, GitHub Actions. React/TS | `git clone` + копирование `.claude/` |
| [claude-howto](https://github.com/luongnv89/claude-howto) (luongnv89) | — | Примеры скиллов (code-review, brand-voice, doc-generator), субагентов, команд | `cp -r 03-skills/code-review ~/.claude/skills/` |
| [claude-md-examples](https://github.com/ArthurClune/claude-md-examples) (ArthurClune) | — | Примеры CLAUDE.md для разных проектов | Ручное копирование |
| [claude-code-guide](https://github.com/zebbern/claude-code-guide) (zebbern) | — | Гайд + ~60 скиллов по безопасности, чит-шит по командам | Ручное копирование |
| [awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) (VoltAgent) | — | 61 скилл, включая официальные от Sentry, Trail of Bits, Expo, Hugging Face | Ручное копирование |

---

## 2. Скиллы и агенты по категориям

### 2.1. Официальные (встроенные в Claude Code)

| Название | Описание |
|----------|----------|
| `pptx` | Создание и редактирование PowerPoint презентаций |
| `xlsx` | Создание таблиц, анализ данных, отчёты с графиками |
| `docx` | Создание и редактирование Word документов |
| `pdf` | Генерация PDF документов и отчётов |
| `skill-creator` | Создание новых скиллов, измерение их производительности |
| `deep-research` | Глубокое исследование темы через Explore агент |
| `explain-code` | Объяснение кода через аналогии и ASCII-диаграммы |
| `pr-summary` | Суммаризация PR через GitHub CLI |

### 2.2. Агенты (everything-claude-code)

| Название | Описание |
|----------|----------|
| `planner` | Планирование фичей, определение зависимостей и рисков |
| `code-reviewer` | Автоматический код-ревью по чеклисту (TS, ошибки, паттерны) |
| `tdd-guide` | Гид по TDD: тесты → реализация → рефакторинг |
| `security-reviewer` | Проверка безопасности кода, поиск уязвимостей |
| `documentation-writer` | Генерация документации, README, API docs |
| `test-engineer` | Написание тестов, покрытие 80%+ |
| `implementation-agent` | Реализация фичей по плану |

### 2.3. Скиллы (everything-claude-code)

| Название | Описание |
|----------|----------|
| `tdd-workflow` | Полный воркфлоу Test-Driven Development |
| `frontend-patterns` | Паттерны фронтенд-разработки (React, TS) |
| `backend-patterns` | Паттерны бэкенд-разработки (API, DB) |
| `coding-standards` | Стандарты и конвенции кода |
| `continuous-learning` | Автоизвлечение паттернов из сессий для переиспользования |
| `search-first` | Поиск существующих решений перед написанием нового кода |
| `cost-aware-llm-pipeline` | Оптимизация затрат на LLM API вызовы |
| `skill-stocktake` | Инвентаризация и оценка имеющихся скиллов |
| `security-scan` (AgentShield) | Сканирование конфигов на уязвимости (1282 теста, 102 правила) |

### 2.4. Команды (everything-claude-code)

| Команда | Описание |
|---------|----------|
| `/plan` | Планирование фичи с агентом-планировщиком |
| `/skill-create` | Генерация скиллов из git-истории проекта |
| `/instinct-status` | Показать выученные инстинкты с уровнями уверенности |
| `/evolve` | Кластеризация инстинктов в скиллы |
| `/sessions` | Управление историей сессий |
| `/codex-setup` | Генерация codex.md для совместимости с OpenAI Codex CLI |

### 2.5. Топ скиллы (antigravity-awesome-skills)

| Название | Описание |
|----------|----------|
| `docker-containerization` | Docker: multi-stage builds, оптимизация образов, безопасность, Compose |
| `supabase-auth-nextjs` | Интеграция Supabase Auth с Next.js App Router |
| `clean-code` | Принципы Clean Code Роберта Мартина для ревью и рефакторинга |
| `nextjs-app-router` | Паттерны Next.js App Router: Server Components, data fetching |
| `prisma-orm` | Prisma: схемы, миграции, оптимизация запросов, отношения |
| `fullstack-development` | React + Next.js + Node.js + GraphQL + PostgreSQL |
| `frontend-design` | Продакшн UI с авторским дизайном, не generic AI |
| `three-js-3d` | Three.js, React Three Fiber, WebGL, 3D для веба |

### 2.6. Безопасность (antigravity-awesome-skills)

| Название | Описание |
|----------|----------|
| `ethical-hacking-methodology` | Полный гайд по этичному хакингу и пентестингу |
| `api-security-best-practices` | Аудит API по стандартам OWASP |
| `auth-implementation-patterns` | JWT, OAuth2, управление сессиями |
| `backend-security-coder` | Безопасные практики бэкенд-кодинга |
| `frontend-security-coder` | XSS-превенция и клиентская безопасность |

### 2.7. Django/Python (everything-claude-code)

| Название | Описание |
|----------|----------|
| `django-patterns` | Паттерны Django: модели, views, middleware |
| `django-security` | Безопасность Django-приложений |
| `django-tdd` | TDD для Django проектов |

### 2.8. Java/Spring (everything-claude-code)

| Название | Описание |
|----------|----------|
| `spring-boot-patterns` | Паттерны Spring Boot приложений |
| `spring-boot-security` | Безопасность Spring Boot |
| `spring-boot-tdd` | TDD для Spring Boot |

### 2.9. React/TS (claude-code-showcase)

| Название | Описание |
|----------|----------|
| `design-review` | Автоматический UI/UX ревью с субагентами |
| `pr-review` | Автоматический PR ревью через GitHub Actions |
| `onboard` | Глубокое исследование задачи перед реализацией |

### 2.10. Шаблоны (claude-howto)

| Название | Описание |
|----------|----------|
| `code-review` | Скилл код-ревью со скриптами и шаблонами |
| `brand-voice` | Скилл для поддержания стиля бренда в тексте |
| `doc-generator` | Генерация документации с Python-скриптом |

---

## 3. Бандлы по ролям

| Роль | Скиллы | Источник |
|------|--------|----------|
| **Web-разработчик** | fullstack-development, nextjs-app-router, prisma-orm, frontend-design, clean-code, docker-containerization | antigravity |
| **Security-инженер** | ethical-hacking-methodology, api-security-best-practices, auth-implementation-patterns, backend-security-coder, frontend-security-coder, security-scan | antigravity + ECC |
| **Backend Python/Django** | django-patterns, django-security, django-tdd, backend-patterns, coding-standards | ECC |
| **Backend Java/Spring** | spring-boot-patterns, spring-boot-security, spring-boot-tdd, coding-standards | ECC |
| **React/TypeScript** | frontend-patterns, design-review, pr-review, clean-code, tdd-workflow | ECC + Showcase |
| **DevOps** | docker-containerization, security-scan, ci/cd workflows, GitHub Actions | antigravity + ECC |
| **Все разработчики** | code-reviewer, tdd-guide, planner, continuous-learning, skill-create | ECC |

---

## 4. Релевантность для проекта «Интерпретация»

Проект сейчас на стадии проектирования (документация, без кода). При переходе к реализации наиболее полезны:

| Скилл/агент | Зачем |
|-------------|-------|
| `planner` | Планирование фичей перед реализацией (дополнение к PLAN.md) |
| `code-reviewer` | Автоматический ревью Python кода (OpenClaw, агенты) |
| `security-scan` | Проверка MCP конфигов и Docker на уязвимости |
| `tdd-workflow` | TDD для пайплайна сцен и агентов |
| `docker-containerization` | Оптимизация Docker-стека (Qdrant + Neo4j + Ollama) |
| `cost-aware-llm-pipeline` | Оптимизация затрат на 18-22 LLM-вызова за тик |
| `continuous-learning` | Извлечение паттернов из отладки агентов |
| `backend-patterns` | Паттерны для Python-бэкенда (API, DB) |
| `coding-standards` | Единые стандарты кода для всех участников |

> **Примечание:** everything-claude-code (ECC) — самый зрелый набор. Рекомендуется начать с него при старте реализации.
