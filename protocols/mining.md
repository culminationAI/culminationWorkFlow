# Mining Protocol

## Overview

Structured knowledge extraction from documents, conversations, and external sources into Neo4j graph + Qdrant vectors. Cross-project capability.

## Pipeline

```
1. Registry Check → what's mined, what's queued
2. Queue Priority → by domain weight + freshness
3. Research → parallel agents extract knowledge
4. Validate → schema compliance, dedup check
5. Save → Neo4j + Qdrant with _source tag
6. Update Registry → mark completed, record stats
```

## Source Attribution

Every mined artifact MUST be tagged:
- `_source: "miner:personal"` — mining personal data
- `_source: "miner:{project}"` — mining project-specific docs (replace with actual project name)
- `_source: "miner:external"` — mining web/external sources

## Mining Processes

| Process | Template | What it extracts |
|---------|----------|-----------------|
| architecture | `prompts/architecture-mining-prompt-v1.0.md` | System components, relationships, patterns |
| egregore | `prompts/egregore-mining-prompt-v2.1.md` | Collective archetypes, cultural patterns |
| sense | `prompts/sense-mining-prompt-v1.0.md` | Sensory experiences, perceptual patterns |

## Tools

```bash
# Registry management
python3 miner/tools/registry.py status
python3 miner/tools/registry.py queue

# Validation
python3 miner/tools/validate.py miner/results/egregores/example.json

# Cross-domain bridging (post-mining)
python3 miner/tools/bridge.py --domains egregores,senses
```

## Three Layers

1. **Domain Mining** — isolated, each process owns its nodes
2. **Bridge Protocol** — post-mining cross-domain connections
3. **Unified Queries** — read-only across all domains

## Bridge Relations

Cross-domain links created after mining:
- `EVOKES_SENSE` — egregore → sense
- `CRYSTALLIZES_AS` — sense → egregore
- `FUELED_BY` — egregore → sense
- `DISSOLVES_THROUGH` — egregore → sense
- `DUAL_NATURE` — bidirectional
