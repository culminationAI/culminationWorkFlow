---
name: memory-manager
description: Direct memory storage and retrieval bypassing mem0 LLM extraction. Use when: (1) saving conversation facts/decisions/events to long-term memory, (2) searching memory for context, (3) deduplicating or cleaning memory records, (4) bulk memory operations. Replaces mem0.add_memory with direct Qdrant+Neo4j writes using Claude's own extraction. NOT for: project file operations, code tasks, or anything unrelated to persistent memory.
---

# Memory Manager

Direct memory pipeline: Claude extracts facts → embeds via Ollama bge-m3 → stores in Qdrant + Neo4j.
No secondary LLM needed. Zero extra API cost.

## Architecture

```
Claude (already understands context)
  ↓ extracts structured facts
  ↓
scripts/memory_write.py
  ├── Ollama bge-m3 → embedding (1024d)
  ├── Qdrant → vector upsert (collection: workflow_memory)
  └── Neo4j → entity/relation upsert (bolt://localhost:7687)
```

## Operations

### 1. Add memories (replaces mem0.add_memory)

Extract facts from conversation yourself. Format as JSON array:

```json
[
  {
    "text": "Balance is 81907 RUB as of 2026-03-01",
    "user_id": "user",
    "agent_id": "finance-manager",
    "metadata": {"type": "financial_snapshot", "date": "2026-03-01"},
    "entities": [
      {"name": "user", "type": "person"},
      {"name": "bank_balance", "type": "metric", "value": "81907 RUB"}
    ],
    "relations": [
      {"source": "user", "relation": "has_balance", "target": "bank_balance"}
    ]
  }
]
```

Run: `python3 scripts/memory_write.py '<JSON_ARRAY>'`

Or pipe from file: `python3 scripts/memory_write.py --file /tmp/memories.json`

### 2. Search memories

```bash
python3 scripts/memory_search.py "query text" --limit 10
```

### 3. Delete/deduplicate

```bash
python3 scripts/memory_dedupe.py --dry-run
python3 scripts/memory_dedupe.py --execute
```

### 4. Cleanup garbage records

```bash
python3 scripts/memory_cleanup.py --pattern "loves to play cricket" --dry-run
```

## Extraction Guidelines

When extracting facts from conversation, follow these rules:

1. **English only** for memory text (≤200 tokens per record)
2. **One concept per record** — but meaningful, not "Drank beer"
3. **Include temporal context** — dates, timeframes
4. **Deduplicate mentally** — don't store what's already in memory
5. **Categorize** with metadata.type: `financial_snapshot | biography | relationship | social | project_update | decision | preference | task | pattern | health | dream | networking | conversation`
6. **Extract entities** for graph: person, place, organization, project, metric, event
7. **Extract relations**: works_at, lives_near, met_at, has_balance, completed, plans_to, etc.

## Config

All connection params from `secrets/.env`:
- Qdrant: `http://localhost:6333`, collection `workflow_memory`
- Neo4j: `bolt://localhost:7687`, user `neo4j`, password from env
- Ollama: `http://localhost:11434`, model `bge-m3`
