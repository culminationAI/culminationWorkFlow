# Coordinator Workflow

Multi-agent workflow for Claude Code: coordinator + 8 specialized subagents + persistent memory layer.

## Quick Start

```bash
unzip workflow.zip
cd workflow
chmod +x setup.sh
./setup.sh
```

## Prerequisites

| Tool | Required | Purpose |
|------|----------|---------|
| Docker | yes | Qdrant (vectors) + Neo4j (graph) |
| Python 3.9+ | yes | Memory scripts |
| Node.js 18+ | yes | MCP servers (npx) |
| Ollama | yes | Embeddings (bge-m3, local) |
| uv/uvx | recommended | MCP servers (neo4j, qdrant, semgrep) |

## Architecture

```
You (user)
  ↓
Coordinator (CLAUDE.md)
  ├── classifies request (T1-T5)
  ├── searches memory + protocols
  └── dispatches to subagent
        ↓
8 Subagents (.claude/agents/)
  ├── narrative-designer    — psychology, dramaturgy, characters
  ├── data-architect        — Neo4j, Qdrant, GraphRAG, data modeling
  ├── engineer              — Python, Docker, API, scripts
  ├── llm-engineer          — prompts, context engineering, model routing
  ├── science-researcher    — physics, chemistry, biology
  ├── humanities-researcher — psychology, sociology, linguistics
  ├── consciousness-researcher — consciousness, mysticism, esotericism
  └── knowledge-curator     — YAML, chunking, cross-refs, catalog
        ↓
Memory Layer (Qdrant + Neo4j + Ollama)
  ├── memory/scripts/memory_search.py  — vector search
  ├── memory/scripts/memory_write.py   — embed + store
  └── memory/scripts/memory_dedupe.py  — deduplication
```

## Directory Structure

```
workflow/
├── CLAUDE.md               — coordinator config (edit ## Project)
├── .claude/agents/          — 9 subagent definitions
├── .mcp.json                — symlink → mcp/mcp.json
├── protocols/               — 6 operational protocols
├── memory/
│   ├── scripts/             — 6 Python scripts
│   ├── CLAUDE.md            — memory layer role
│   └── SKILL.md             — skill definition
├── mcp/
│   ├── mcp.json             — 8 MCP server configs
│   ├── servers.md           — server documentation
│   └── with-env.sh          — env loader
├── infra/
│   └── docker-compose.yml   — Qdrant + Neo4j
├── docs/tech/               — reference docs (4 domains)
├── secrets/
│   └── .env                 — API keys (fill after setup)
├── setup.sh                 — deployment script
└── README.md                — this file
```

## After Setup

1. Edit `secrets/.env` — fill in your API keys
2. Edit `CLAUDE.md` — configure `## Project` section for your domain
3. Open this directory in Claude Code
4. The workflow activates automatically via CLAUDE.md

## Protocols

| Protocol | When it triggers |
|----------|-----------------|
| Memory | Before/after significant tasks |
| Evolution | After user corrections |
| Query Optimization | Every request (T1-T5 classification) |
| Agent Communication | Every T3+ subagent dispatch |
| Context Engineering | Assembling subagent prompts |
| Mining | Knowledge extraction |

## Memory Layer

Zero API cost. Ollama bge-m3 (local) → Qdrant + Neo4j.

```bash
# Search
python3 memory/scripts/memory_search.py "what I decided about auth"

# Write
python3 memory/scripts/memory_write.py '[{"text":"Chose JWT for auth","user_id":"user","agent_id":"coordinator","metadata":{"type":"decision"}}]'

# Graph traversal
python3 memory/scripts/memory_search.py "auth" --graph
```
