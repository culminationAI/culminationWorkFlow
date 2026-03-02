#!/usr/bin/env python3
"""Direct memory writer: embed via Ollama bge-m3, store in Qdrant + Neo4j.

Usage:
    python3 memory_write.py '<json_array>'
    python3 memory_write.py --file /tmp/memories.json

Each record in the array:
{
    "text": "fact to remember",
    "user_id": "user",
    "agent_id": "finance-manager",
    "metadata": {"type": "...", ...},
    "entities": [{"name": "...", "type": "..."}],        # optional
    "relations": [{"source": "...", "relation": "...", "target": "..."}]  # optional
}
"""

from __future__ import annotations

import json
import sys
import uuid
import hashlib
import argparse
from datetime import datetime, timezone
from typing import Any

import os
import requests

# --- Config ---
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = "bge-m3"
EMBED_DIMS = 1024

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION = "workflow_memory"

NEO4J_URL = os.environ.get("NEO4J_URL", "http://localhost:7474")
NEO4J_USER = os.environ.get("NEO4J_USERNAME", "neo4j")
NEO4J_PASS = os.environ.get("NEO4J_PASSWORD", "workflow")
NEO4J_DB = "neo4j"


def get_embedding(text: str) -> list[float]:
    """Get embedding from Ollama bge-m3."""
    resp = requests.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": EMBED_MODEL, "input": text},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    # Ollama returns {"embeddings": [[...]]}
    embeddings = data.get("embeddings", [])
    if embeddings:
        return embeddings[0][:EMBED_DIMS]
    raise ValueError(f"No embeddings returned: {data}")


def qdrant_upsert(point_id: str, vector: list[float], payload: dict[str, Any]) -> None:
    """Upsert a single point to Qdrant."""
    resp = requests.put(
        f"{QDRANT_URL}/collections/{COLLECTION}/points",
        json={
            "points": [
                {
                    "id": point_id,
                    "vector": vector,
                    "payload": payload,
                }
            ]
        },
        timeout=10,
    )
    resp.raise_for_status()


def neo4j_run(statement: str, parameters: dict | None = None) -> list:
    """Execute a Cypher statement via Neo4j HTTP API."""
    body: dict[str, Any] = {"statements": [{"statement": statement}]}
    if parameters:
        body["statements"][0]["parameters"] = parameters
    resp = requests.post(
        f"{NEO4J_URL}/db/{NEO4J_DB}/tx/commit",
        json=body,
        auth=(NEO4J_USER, NEO4J_PASS),
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    errors = data.get("errors", [])
    if errors:
        raise RuntimeError(f"Neo4j errors: {errors}")
    return data.get("results", [])


def neo4j_upsert_entities_and_relations(
    entities: list[dict], relations: list[dict], user_id: str
) -> None:
    """Upsert entities and relations to Neo4j graph."""
    if not entities and not relations:
        return

    for ent in entities:
        name = ent["name"].lower().replace(" ", "_")
        ent_type = ent.get("type", "entity").lower().replace(" ", "_")
        props = {k: v for k, v in ent.items() if k not in ("name", "type")}
        props["user_id"] = user_id
        props["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Use __User__ label pattern consistent with mem0
        cypher = (
            f"MERGE (n:`{ent_type}` {{name: $name}}) "
            f"SET n += $props"
        )
        neo4j_run(cypher, {"name": name, "props": props})

    for rel in relations:
        source = rel["source"].lower().replace(" ", "_")
        target = rel["target"].lower().replace(" ", "_")
        relation = rel["relation"].upper().replace(" ", "_")

        cypher = (
            f"MERGE (a {{name: $source}}) "
            f"MERGE (b {{name: $target}}) "
            f"MERGE (a)-[r:`{relation}`]->(b) "
            f"SET r.updated_at = $ts"
        )
        neo4j_run(cypher, {
            "source": source,
            "target": target,
            "ts": datetime.now(timezone.utc).isoformat(),
        })


def write_memories(records: list[dict]) -> dict[str, int]:
    """Write a batch of memory records. Returns counts."""
    ok = 0
    failed = 0

    for i, rec in enumerate(records):
        text = rec["text"]
        user_id = rec.get("user_id", "user")
        agent_id = rec.get("agent_id", "general")
        metadata = rec.get("metadata", {})
        entities = rec.get("entities", [])
        relations = rec.get("relations", [])

        try:
            # 1. Embed
            vector = get_embedding(text)

            # 2. Build payload (compatible with mem0 format)
            point_id = str(uuid.uuid4())
            text_hash = hashlib.md5(text.encode()).hexdigest()
            now = datetime.now(timezone.utc).isoformat()

            payload = {
                "data": text,  # mem0 uses "data" field
                "hash": text_hash,
                "created_at": now,
                "updated_at": None,
                "user_id": user_id,
                "agent_id": agent_id,
            }
            if metadata:
                payload["metadata"] = metadata

            # 3. Qdrant upsert
            qdrant_upsert(point_id, vector, payload)

            # 4. Neo4j graph
            neo4j_upsert_entities_and_relations(entities, relations, user_id)

            ok += 1
            print(f"[{i+1}/{len(records)}] ✓ {text[:60]}")

        except Exception as e:
            failed += 1
            print(f"[{i+1}/{len(records)}] ✗ {text[:40]}... ERROR: {e}")

    return {"ok": ok, "failed": failed}


def main():
    parser = argparse.ArgumentParser(description="Direct memory writer")
    parser.add_argument("json_data", nargs="?", help="JSON array of records")
    parser.add_argument("--file", "-f", help="Read records from JSON file")
    args = parser.parse_args()

    if args.file:
        with open(args.file) as f:
            records = json.load(f)
    elif args.json_data:
        records = json.loads(args.json_data)
    else:
        # Read from stdin
        records = json.load(sys.stdin)

    if not isinstance(records, list):
        records = [records]

    print(f"Writing {len(records)} memories...")
    result = write_memories(records)
    print(f"\nDone: {result['ok']} ok, {result['failed']} failed")
    sys.exit(1 if result["failed"] > 0 else 0)


if __name__ == "__main__":
    main()
