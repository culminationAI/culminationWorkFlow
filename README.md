# CulminationAI Workflow

Multi-agent orchestration framework for Claude Code. Transforms a single AI assistant into a coordinated team of specialized agents with persistent memory, structured protocols, and self-improvement capabilities.

## Prerequisites

- [Claude Code](https://claude.ai/code) CLI installed
- Docker Desktop (for Qdrant + Neo4j memory layer)
- Python 3.9+
- Node.js 18+ (for MCP servers)
- Git
- [Ollama](https://ollama.ai) (for local embeddings)

## Install

### Quick (one-liner)

```bash
cd /path/to/your/project
curl -sL https://raw.githubusercontent.com/culminationAI/culminationWorkFlow/main/install.sh | bash
```

### Manual

```bash
cd /path/to/your/project
git clone https://github.com/culminationAI/culminationWorkFlow.git /tmp/workflow
cp -r /tmp/workflow/{.claude,protocols,memory,mcp,infra,secrets,setup.sh,CLAUDE.md,user-identity.md} ./
chmod +x setup.sh
rm -rf /tmp/workflow
```

Both methods install workflow files into your current project directory without overwriting existing files.

> **Telegram bot** (optional): copy `bot/` directory manually from the repo if you want remote access via Telegram.

## Next Steps

1. Run `./setup.sh --check` to verify all prerequisites
2. Run `./setup.sh` to deploy infrastructure (Qdrant, Neo4j, Ollama embeddings)
3. Edit `secrets/.env` — fill in your API keys
4. Open your project in Claude Code
5. Claude will detect the workflow and start initialization automatically (9 phases)
6. Follow the prompts to configure agents, preferences, and project-specific protocols

## Architecture

```
Coordinator (CLAUDE.md)
  ├── pathfinder        — project exploration, memory management, validation
  ├── protocol-manager  — protocol lifecycle, organization, indexing
  ├── engineer          — code, infrastructure, deployment, testing
  ├── llm-engineer      — prompt design, agent creation, context engineering
  └── [domain agents]   — created during initialization based on project type
```

The **coordinator** is the main Claude Code session. It classifies requests (T1-T5), routes to specialized agents, and synthesizes results. It never executes domain tasks directly.

## Initialization

On first session, the workflow automatically:

1. **Explores** your project (pathfinder scans codebase)
2. **Learns** your preferences (name, style, priorities)
3. **Adapts** by creating domain-specific agents and protocols
4. **Deploys** infrastructure (Docker: Qdrant + Neo4j)
5. **Verifies** everything works (memory, agents, protocols)
6. **Evolves** — runs evolution cycle, graduating from v0.1 → v1.0

## Memory Layer (Zero API Cost)

Persistent memory powered by local models:

- **Qdrant** — vector store for semantic search (1024d embeddings)
- **Neo4j** — knowledge graph for entity relationships
- **Ollama bge-m3** — local embedding model (no API calls)

Memory is managed by the pathfinder agent and accessed through scripts in `memory/scripts/`.

## Protocols

Behavioral patterns organized in `protocols/`:

| Directory | Purpose |
|-----------|---------|
| `core/` | Initialization, evolution, coordination, query optimization |
| `agents/` | Agent creation, communication contracts, meta-protocol |
| `knowledge/` | Exploration, memory rules, context engineering |
| `quality/` | Testing, benchmarks, cloning for safe evolution |
| `project/` | Project-specific protocols (created during init) |

Protocols are loaded on demand, not all at once. See `protocols/README.md` for details.

## Agents

### Base Agents (Always Available)

| Agent | Specialty |
|-------|-----------|
| **pathfinder** | Project exploration, memory management, validation, connection mapping |
| **protocol-manager** | Protocol CRUD, directory organization, indexing |
| **engineer** | Python, Docker, APIs, scripts, tests, infrastructure |
| **llm-engineer** | Prompt design, context engineering, model routing, agent creation |

### Domain Agents (Created During Initialization)

Selected based on your project type:

| Project Type | Typical Agents |
|--------------|----------------|
| AI/ML | data-architect, science-researcher |
| Web App | engineer (frontend), engineer (backend) |
| Data Pipeline | data-architect, engineer |
| Content/Docs | knowledge-curator, humanities-researcher |
| Game Dev | narrative-designer, engineer |

## Query Optimization

Every request is classified by tier:

| Tier | Complexity | Handled By |
|------|-----------|------------|
| T1 | Simple lookup | Direct tool (no agent) |
| T2 | Small edit | General-purpose agent |
| T3-T5 | Complex task | Specialized agent(s) |

This saves 50-70% of token budget by avoiding unnecessary agent dispatches.

## Telegram Bot

Optional remote interface via Telegram:

- Each thread maps to a project
- Streaming responses with markdown
- Model switching per thread
- Session persistence

Set up during initialization if you provide a bot token.

## User Identity

The workflow learns over time by maintaining `user-identity.md`:

- Communication preferences
- Work patterns
- Key decisions
- Project milestones

Updated automatically through evolution corrections.

## Research Participation

Optionally contribute anonymized project data (architecture patterns, agent configurations) to [culminationAI/research-data](https://github.com/culminationAI/research-data). All data is visible in the `research/` directory before any push. You can opt in/out during initialization.

## Versioning

- **0.1** — fresh install, pre-initialization
- **1.0** — initialization complete, all systems operational
- **1.x** — incremented by evolution protocol on improvements

## Directory Structure

```
.claude/agents/          — agent definitions
protocols/               — behavioral protocols (5 subdirectories)
memory/scripts/          — memory management scripts
mcp/                     — MCP server configurations
infra/                   — Docker Compose for Qdrant + Neo4j
bot/                     — Telegram bot (optional)
secrets/                 — environment variables (.env)
docs/tech/               — technical reference documentation
```

## License

MIT
