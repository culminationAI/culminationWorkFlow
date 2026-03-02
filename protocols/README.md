# Protocols Directory

Protocols are reusable behavioral patterns for the coordinator and agents. This README describes the directory structure and how to find, use, and create protocols.

## Directory Structure

```
protocols/
├── README.md              ← this file
├── core/                  ← fundamental workflow mechanics
│   ├── initialization.md  ← project onboarding (via evolution)
│   ├── evolution.md       ← self-improvement pipeline
│   ├── coordination.md    ← parallel agent orchestration
│   └── query-optimization.md ← T1-T5 tier classification
├── agents/                ← agent lifecycle and communication
│   ├── agent-creation.md  ← creating new domain agents
│   ├── agent-communication.md ← dispatch/response format
│   └── meta.md            ← protocol lifecycle (meta-protocol)
├── knowledge/             ← memory, exploration, context
│   ├── exploration.md     ← pathfinder operations
│   ├── memory.md          ← memory layer usage rules
│   └── context-engineering.md ← token budgets, compression
├── quality/               ← testing and verification
│   ├── testing.md         ← benchmarks, evolution pipeline
│   └── cloning.md         ← isolated instances for testing
└── project/               ← project-specific protocols
    └── (created during initialization by protocol-manager)
```

## How to Find a Protocol

1. **By category** — browse subdirectories above
2. **By keyword** — `grep -ri "keyword" protocols/`
3. **By trigger** — check the protocol index in CLAUDE.md
4. **By agent** — protocol-manager can search and recommend

## How to Use a Protocol

1. Load on demand — read only when needed, not all at once
2. Extract relevant sections — don't inject the entire protocol if only one part applies
3. Adapt to context — protocols are templates, not rigid scripts
4. Document deviations — if you skip steps, note why

## How to Create a Protocol

See `agents/meta.md` for the full creation process and template.

Quick summary:
1. Check existing protocols for overlap
2. Choose the correct subdirectory
3. Draft following the template (Overview, Triggers, Process, Rules, Examples)
4. Keep under 150 lines
5. Register in this README and in CLAUDE.md

## Categories

| Directory | Purpose | Example Protocols |
|-----------|---------|-------------------|
| `core/` | Workflow fundamentals | How the system boots, evolves, optimizes |
| `agents/` | Agent lifecycle | How to create agents, communicate between them |
| `knowledge/` | Information management | How to explore, remember, manage context |
| `quality/` | Verification | How to test, benchmark, clone for safety |
| `project/` | Project-specific | Custom rules for the current project |
