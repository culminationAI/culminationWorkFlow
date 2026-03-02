# Self-Architecture

Living documentation of the workflow's adaptive architecture. Updated by pathfinder (self-explore mode) and the self-build-up protocol.

## Contents

| File | Purpose | Updated by |
|------|---------|------------|
| `capability-map.md` | Current system capabilities | pathfinder (auto-generated) |
| `build-registry.json` | Active + buffered builds | self-build-up protocol |
| `spec-registry.json` | Atomic capability units (specs) — composable building blocks for builds | self-build-up protocol |
| `gap-analysis-log.md` | History of gap analyses | gap-analysis protocol |
| `smoke-tests/` | Validation scenarios | manual / protocol-manager |
| `request-history.json` | T3+ request log for trajectory analysis | coordinator (auto-append) |
| `request-history-archive.json` | Archived request history (overflow) | coordinator (auto-archive) |

## Concept

The workflow is **self-aware** — it knows what it can and cannot do. When a task exceeds current capabilities, instead of failing or producing suboptimal results, the system:

1. **Detects the gap** via gap analysis (5 dimensions: agents, protocols, memory, MCP, knowledge)
2. **Classifies** it: KNOWLEDGE gap (just need more data) vs STRUCTURAL gap (need new capabilities)
3. **Acts**: strengthen memory OR create a build
4. **Spec** = atomic capability unit (one agent, one protocol, one MCP config, or one rule set). Specs are reusable building blocks, registered in `spec-registry.json`, each with its own state (AVAILABLE / IN_USE).
5. **Build** = temporary architectural extension composed of one or more specs, with a TTL. Builds reference specs by ID — no duplication.
6. **When no longer needed**, the build downgrades to a buffer — stored with full context of WHY it was created. Specs return to AVAILABLE state unless shared by another active build.
7. **Re-activation** on demand — the build can be "worn" again, or a single spec cherry-picked without recreating the whole build.
8. **Standalone activation** — when only one dimension is missing, a single spec can be activated directly without creating a full build (max 3 standalone specs at once).

## Protocols

- **Self Build-Up**: `protocols/core/self-build-up.md` — master lifecycle
- **Gap Analysis**: `protocols/core/gap-analysis.md` — detection algorithm
- **Evolution**: `protocols/core/evolution.md` — reactive evolution (corrections)
- **Exploration**: `protocols/knowledge/exploration.md` — pathfinder modes including self-explore

## Build Lifecycle

```
[DRAFT] → [ACTIVE] → [BUFFERED] → [ARCHIVED]
              ↑            |
              +---- re-activate ----+
```
