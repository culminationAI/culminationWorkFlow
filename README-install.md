# CulminationAI Workflow

Multi-agent orchestration framework for Claude Code. Adds persistent memory, specialized agents, and structured protocols to any project.

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

## Documentation

Full documentation is available in README.md after installation.

## License

MIT
