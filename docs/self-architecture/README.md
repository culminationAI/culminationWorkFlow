# Self-Architecture

Living documentation of the workflow's adaptive architecture. Updated by pathfinder (self-explore mode) and the self-evolution protocol.

## Contents

| File | Purpose | Updated by |
|------|---------|------------|
| `capability-map.md` | Current system capabilities | pathfinder (auto-generated) |
| `body-registry.json` | Active + buffered evolution bodies | self-evolution protocol |
| `gap-analysis-log.md` | History of gap analyses | gap-analysis protocol |
| `smoke-tests/` | Validation scenarios | manual / protocol-manager |

## Concept

The workflow is **self-aware** — it knows what it can and cannot do. When a task exceeds current capabilities, instead of failing or producing suboptimal results, the system:

1. **Detects the gap** via gap analysis (5 dimensions: agents, protocols, memory, MCP, knowledge)
2. **Classifies** it: KNOWLEDGE gap (just need more data) vs STRUCTURAL gap (need new capabilities)
3. **Acts**: strengthen memory OR create an evolution body
4. **Evolution body** = temporary architectural extension (new agents, protocols, rules) with a TTL
5. **When no longer needed**, the body downgrades to a buffer — stored with full context of WHY it was created
6. **Re-activation** on demand — the body can be "worn" again, or pieces cherry-picked

## Protocols

- **Self-Evolution**: `protocols/core/self-evolution.md` — master lifecycle
- **Gap Analysis**: `protocols/core/gap-analysis.md` — detection algorithm
- **Evolution**: `protocols/core/evolution.md` — reactive evolution (corrections)
- **Exploration**: `protocols/knowledge/exploration.md` — pathfinder modes including self-explore

## Body Lifecycle

```
[DRAFT] → [ACTIVE] → [BUFFERED] → [ARCHIVED]
              ↑            |
              +---- re-activate ----+
```
