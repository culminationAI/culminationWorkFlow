# Memory Protocol

## Overview

Zero-cost persistent episodic memory. Claude extracts facts → Ollama bge-m3 embeds → Qdrant vectors + Neo4j graph.

## Tools

```bash
# Search (vector, ~1s)
python3 memory/scripts/memory_search.py "query text" --limit 10

# Search (graph traversal)
python3 memory/scripts/memory_search.py "query" --graph

# Filter by source project
python3 memory/scripts/memory_search.py "query" --source personal

# Write (~2s)
python3 memory/scripts/memory_write.py '[{...}]' --source personal

# Deduplication
python3 memory/scripts/memory_dedupe.py

# Integrity check
python3 memory/scripts/memory_verify.py
```

## Write Format

```json
[{
  "text": "English, ≤200 tokens, one fact per record",
  "user_id": "user",
  "agent_id": "coordinator|narrative-designer|...",
  "metadata": {
    "type": "decision|preference|evolution|task|contract|blocker",
    "source_project": "personal|{project}|miner:personal|..."
  },
  "entities": [{"name": "Entity Name", "type": "person|project|metric|concept"}],
  "relations": [{"source": "A", "relation": "WORKS_ON", "target": "B"}]
}]
```

## Rules

1. **Search before write** — avoid duplicates
2. **English only** — max 200 tokens per record
3. **One fact per record** — atomic, searchable
4. **Always tag**: `user_id`, `agent_id`, `metadata.type`, `metadata.source_project`
5. **Session start**: search `"active tasks blockers recent decisions"`
6. **After T3+ work**: store key decisions and outcomes

## When to Store

| Trigger | metadata.type |
|---------|--------------|
| User corrects you | `evolution` (subtype: correction) |
| Wrong agent routed | `evolution` (subtype: routing) |
| Session-end review (T3+ work) | `evolution` (subtype: workflow) |
| User states preference | `preference` |
| Architecture/design decision | `decision` |
| Task completed | `task` |
| Blocker encountered | `blocker` |

## Conflict Resolution

When memory contains contradictory records:
1. Newer record wins (check timestamps)
2. Delete or flag the outdated record
3. Run `memory_dedupe.py` periodically
