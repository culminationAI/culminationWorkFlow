# CulminationAI Workflow

Multi-agent orchestration framework for Claude Code. Adds persistent memory, specialized agents, and structured protocols to any project.

## Prerequisites

- [Claude Code](https://claude.ai/code) CLI installed
- Docker Desktop (for Qdrant + Neo4j memory layer)
- Python 3.9+
- Git

## Install

### Quick (one-liner)

```bash
curl -sL https://raw.githubusercontent.com/culminationAI/culminationWorkFlow/main/install.sh | bash
```

### Manual

```bash
git clone https://github.com/culminationAI/culminationWorkFlow.git /tmp/workflow
cp -r /tmp/workflow/{.claude,protocols,memory,mcp,infra,secrets,setup.sh,CLAUDE.md,user-identity.md} ./
chmod +x setup.sh
rm -rf /tmp/workflow
```

Both methods install workflow files into your current project directory without overwriting existing files.

## Next Steps

1. Open your project in Claude Code
2. Claude will detect the workflow and start initialization automatically
3. Follow the prompts to configure agents and infrastructure

## Documentation

Full documentation is available in README.md after installation.

## License

MIT
