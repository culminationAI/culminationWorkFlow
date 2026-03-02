# Initialization Protocol

## Overview

Bootstrap a new project with the coordinator workflow. Analyzes existing codebase, creates domain-specific agents, configures the coordinator, and deploys infrastructure.

## Triggers

- First run in a new project (CLAUDE.md contains `_WORKFLOW_NEEDS_INIT` marker)
- User requests: "initialize workflow", "bootstrap", "set up agents"

## Process

### Phase 1: Environment Check

1. Verify prerequisites: Docker, Python 3.9+, Node.js 18+, Ollama
2. Run `setup.sh --check` if available
3. Check existing configuration (CLAUDE.md, .claude/agents/) — new project or extension?

### Phase 2: Project Analysis (automatic)

Analyze the existing codebase without asking user:

1. **Languages** — Glob for file extensions: `*.py`, `*.ts`, `*.js`, `*.go`, `*.rs`, `*.java`, `*.rb`, etc.
2. **Frameworks** — check for: `package.json`, `requirements.txt`, `Cargo.toml`, `go.mod`, `pom.xml`, `Gemfile`
3. **Structure** — identify patterns: `src/`, `tests/`, `docs/`, `api/`, `frontend/`, `backend/`
4. **Existing docs** — read README.md, existing CLAUDE.md, config files
5. **Determine archetype**: AI/ML, Web App, Data/Analytics, Content/Research, DevOps, Game, Mobile, Mixed

### Phase 3: Discovery (interactive)

Present analysis to user and ask clarifying questions:

1. Show analysis: "I see a Python/FastAPI project with PostgreSQL and React frontend..."
2. Ask: "What are the project goals? What's the development focus?"
3. Ask: "Which areas need agent support? (backend, frontend, data, research, testing, etc.)"
4. Propose agent roster: "I suggest these agents: engineer + backend-specialist + data-architect. OK?"
5. Adjust based on user feedback

### Phase 4: Agent Creation

1. Create domain agents using `protocols/agent-creation.md`
2. Delegate agent file creation to llm-engineer
3. Update dispatcher.md with new routing entries
4. Update CLAUDE.md subagent table and workspace map

### Phase 5: Infrastructure Deploy

1. Run `setup.sh` for Docker services (Qdrant + Neo4j)
2. Create Qdrant collection: `{project_code}_memory`
3. Pull Ollama embedding model (bge-m3)
4. Verify: `python3 memory/scripts/memory_verify.py --quick`

### Phase 6: Self-Test

1. Run T1 task (direct tool — Glob/Grep) → verify coordinator works
2. Run T2 task (basic subagent dispatch) → verify engineer responds
3. Run T3 task (specialized agent) → verify domain agent works + memory stores
4. Report: "Workflow initialized. N agents, M protocols. Ready."
5. Remove `_WORKFLOW_NEEDS_INIT` marker from CLAUDE.md

## Project Archetypes

| Archetype | Indicators | Suggested Domain Agents |
|-----------|-----------|------------------------|
| AI/ML | .py, torch/tensorflow, model configs | data-architect, ml-researcher, llm-engineer |
| Web App | package.json, React/Vue/Angular, API routes | frontend-eng, backend-eng, designer |
| Data/Analytics | notebooks, SQL, pandas/spark | data-engineer, analyst |
| Content/Research | .md files, knowledge base, references | researcher(s), writer, curator |
| DevOps/Infra | Dockerfile, terraform, k8s manifests | devops-eng, security |
| Science/Academic | LaTeX, data files, citations | researcher(s), analyst |
| Game | Unity/Godot, game assets, shaders | game-designer, engineer |
| Mobile | Swift/Kotlin, Xcode/Android configs | mobile-eng, designer |
| Mixed | Multiple indicators | combine from above |

## Rules

1. ALWAYS interactive — don't decide agent roster without user approval
2. Base agents (engineer, llm-engineer) are non-negotiable — always created
3. Max 8 agents at initial setup (can add more later via agent-creation protocol)
4. All protocols are copied as-is (they are universal)
5. Memory collection name = `{project_code}_memory`
6. If workspace already initialized — ask: "extend or recreate?"
7. Store initialization summary in memory after completion

## Anti-patterns

- Creating too many agents upfront (start with 3-5, add as needed)
- Skipping project analysis (leads to wrong agent selection)
- Not running self-test (silent failures go undetected)
- Initializing over an existing workflow without asking
