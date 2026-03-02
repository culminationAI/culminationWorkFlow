# CLAUDE.md — Memory

## Role

Shared memory layer for all projects. Zero API cost — local Qdrant + Neo4j + Ollama bge-m3.

## Usage

```bash
# Search (~1s)
python3 scripts/memory_search.py "query" --limit 10

# Write (~2s)
python3 scripts/memory_write.py '[{"text": "fact", "user_id": "user", "agent_id": "coordinator"}]'

# Graph search (Neo4j traversal)
python3 scripts/memory_search.py "query" --graph

# Filter by source
python3 scripts/memory_search.py "query" --source personal

# Deduplicate
python3 scripts/memory_dedupe.py

# Verify integrity
python3 scripts/memory_verify.py
```

## Write Format

```json
[{
  "text": "English, ≤200 tokens, one fact per record",
  "user_id": "user",
  "agent_id": "coordinator",
  "metadata": {"type": "decision|preference|evolution|task", "source_project": "personal"},
  "entities": [{"name": "...", "type": "person|project|metric"}],
  "relations": [{"source": "...", "relation": "...", "target": "..."}]
}]
```

## Rules

- All text in **English**, max 200 tokens
- Search before writing — avoid duplicates
- One fact per record
- Always set `user_id`, `agent_id`, `metadata.type`
- Tag with `source_project` for data attribution
