# Smoke Test: Gap Analysis Accuracy

Validates that gap analysis correctly classifies four distinct scenarios: no gap, knowledge gap, structural gap, and buffered body match.

**Protocol under test:** `protocols/core/gap-analysis.md`
**Log file:** `docs/self-architecture/gap-analysis-log.md`
**Registry:** `docs/self-architecture/build-registry.json`

---

## Setup

Before running:
- `docs/self-architecture/capability-map.md` must exist (run pathfinder self-explore first if missing).
- Memory layer must be accessible (`python3 memory/scripts/memory_search.py` functional).
- `build-registry.json` must be accessible.
- Each test runs a **deep scan** unless noted otherwise.

Score dimensions referenced: `AGENT_COVERAGE`, `PROTOCOL_COVERAGE`, `MEMORY_COVERAGE`, `MCP_COVERAGE`, `KNOWLEDGE_COVERAGE` (each 0.0–1.0).

---

## Steps

### T1 — No-gap scenario

**Input task:** "Find where the dispatcher protocol is defined."

**Context:** This is a T1 task (find/locate). The dispatcher is a known core protocol documented in CLAUDE.md, indexed in capability-map.md, with likely memory records. All 5 dimensions should score high.

**Procedure:**
1. Run lightweight gap analysis on the input task (no subagent dispatch required).
2. Capture the gap analysis output.

**Expected output:**
- `overall_score > 0.8`
- `gaps` array: empty (or all requirements score >= 0.8)
- `recommendation`: none (or "No action needed")
- Classification: no gap triggered

**Verify:**
- Log entry appended to `gap-analysis-log.md` with `overall_score > 0.8`.
- No build creation proposed.
- No memory strengthening proposed.

**Pass condition:** Score > 0.8. No gaps. No action recommended.

---

### T2 — Knowledge gap

**Input task:** "Write a Kubernetes deployment manifest for the bot."

**Context:** Kubernetes is outside the workflow's current documented domain. No agent covers K8s deployment. However, the `engineer` agent covers infrastructure generically (AGENT partial), and a general deployment protocol exists (PROTOCOL partial). The gap is in MEMORY and KNOWLEDGE — the system lacks K8s-specific context.

**Procedure:**
1. Run deep gap analysis on the input task.
2. Score per dimension for the "Kubernetes deployment" requirement:
   - `AGENT_COVERAGE`: 0.5 (engineer covers infra generically, not K8s specifically)
   - `PROTOCOL_COVERAGE`: 0.5 (deployment protocols exist but not K8s-specific)
   - `MEMORY_COVERAGE`: < 0.5 (search "kubernetes deployment manifest" → 0 or very few results)
   - `MCP_COVERAGE`: 1.0 (no special MCP tool needed)
   - `KNOWLEDGE_COVERAGE`: < 0.5 (no K8s docs in `docs/tech/`)

**Expected output:**
- Classification: `KNOWLEDGE` gap
- `MEMORY_COVERAGE < 0.5` and/or `KNOWLEDGE_COVERAGE < 0.5`
- `AGENT_COVERAGE >= 0.5` and `PROTOCOL_COVERAGE >= 0.5` and `MCP_COVERAGE >= 0.5`
- `recommendation`: `strengthen_memory` (dispatch researchers, web search K8s docs)
- No build creation proposed

**Verify:**
- Log entry classification = `KNOWLEDGE`.
- Recommendation does NOT include `create_build` or `reactivate_build`.
- Recommendation includes `strengthen_memory` or equivalent.

**Pass condition:** KNOWLEDGE classification. Memory/knowledge dimensions below threshold. Agent/protocol/MCP above threshold. Action = strengthen memory.

---

### T3 — Structural gap

**Input task:** "Design real-time WebSocket streaming with Redis pub/sub for the bot."

**Context:** No agent covers WebSocket/Redis. No protocol covers real-time streaming. No MCP server for Redis is configured. This is a multi-dimensional structural gap.

**Procedure:**
1. Run deep gap analysis on the input task.
2. Score per dimension for the "WebSocket + Redis streaming" requirement:
   - `AGENT_COVERAGE`: < 0.5 (no agent with WebSocket/Redis domain)
   - `PROTOCOL_COVERAGE`: < 0.5 (no streaming protocol exists)
   - `MEMORY_COVERAGE`: < 0.5 (search "websocket redis streaming" → likely 0 results)
   - `MCP_COVERAGE`: < 0.5 (no Redis MCP server in active or full profile)
   - `KNOWLEDGE_COVERAGE`: < 0.5 (no docs in `docs/tech/` for Redis or WebSocket)

**Expected output:**
- Classification: `STRUCTURAL` gap
- `AGENT_COVERAGE < 0.5` and `MCP_COVERAGE < 0.5`
- `recommendation`: `create_build` (new agent + protocol needed)
- No buffered build match (none exists yet in this scenario)

**Verify:**
- Log entry classification = `STRUCTURAL`.
- Recommendation = `create_build` (not `reactivate_build`).
- Build creation proposed to coordinator (coordinator must confirm before acting).
- No auto-creation — coordinator presents findings to user first per protocol rule 7.

**Pass condition:** STRUCTURAL classification. Agent and MCP dimensions below threshold. Recommendation = create_build.

---

### T4 — Buffered body match

**Setup (before running analysis):**
1. Insert a test build into `build-registry.json` in `buffered` state:
   ```json
   {
     "id": "test-websocket-body-001",
     "state": "buffered",
     "created": "<ISO8601>",
     "what_task": "Real-time WebSocket streaming with Redis pub/sub — bot integration",
     "components": {
       "agents": [
         {
           "name": "websocket-engineer",
           "file": ".claude/agents/websocket-engineer.md",
           "description": "Handles WebSocket server design, Redis pub/sub integration, real-time event routing"
         }
       ],
       "protocols": [],
       "rules": []
     },
     "ttl_sessions": 10,
     "ttl_days": 14,
     "use_count": 3,
     "last_used": "<ISO8601>"
   }
   ```

**Input task:** Same as T3 — "Design real-time WebSocket streaming with Redis pub/sub for the bot."

**Procedure:**
1. Run deep gap analysis on the same input as T3.
2. At Step "Buffered Build Check" (before recommending build creation), scan `build-registry.json` for buffered builds.
3. Match `what_task` of `test-websocket-body-001` against gap requirements — it overlaps on "WebSocket streaming" and "Redis pub/sub".
4. Also match against `components.agents[].description` — "WebSocket server", "Redis pub/sub" match.

**Expected output:**
- Match found: `test-websocket-body-001`
- `recommendation`: `reactivate_build:test-websocket-body-001`
- No `create_build` recommended (reactivation always preferred over creation)

**Verify:**
- Log entry `recommendation` = `reactivate_build:test-websocket-body-001`.
- `buffered_builds_relevant` in log includes `test-websocket-body-001`.
- Coordinator presents reactivation option to user (not auto-reactivates).

**Cleanup after T4:**
- Remove `test-websocket-body-001` from `build-registry.json`.
- Confirm removal: registry does not contain `id = test-websocket-body-001`.

**Pass condition:** Buffered build detected before create_build is recommended. Recommendation = `reactivate_build:test-websocket-body-001`.

---

### T5: Parallel Gap-Check

**Setup:** Domain with known coverage in capability-map
**Steps:**
1. Simulate T3+ request in a well-covered domain
2. Trigger parallel gap-check (coordinator Track B)
3. Verify: coordinator quick check completes without dispatching pathfinder
4. Verify: gap-analysis-log has entry with `parallel_context` field

**Pass:** No pathfinder dispatch, result logged, main task not blocked

---

### T6: Predictive Analysis

**Setup:** Insert 15 entries with DESIGN-phase verbs into request-history.json
**Steps:**
1. Run deep gap analysis with predictive extension
2. Verify output includes `predictive.current_phase: "DESIGN"`
3. Verify `predicted_next_phase: "IMPLEMENTATION"`
4. Verify `predicted_needs` includes engineer/data-architect capabilities
5. Insert 15 MIXED entries (no dominant verb pattern)
6. Re-run → verify `current_phase: "MIXED"`, no predictions

**Pass:** Phase correctly detected, predictions match phase transition table

---

## Pass Criteria

| Step | Classification | Key condition | Action |
|------|---------------|--------------|--------|
| T1 | No gap | `overall_score > 0.8` | none |
| T2 | KNOWLEDGE | `memory < 0.5`, `agent >= 0.5` | strengthen_memory |
| T3 | STRUCTURAL | `agent < 0.5`, `mcp < 0.5` | create_build |
| T4 | STRUCTURAL | same as T3 + buffered match | reactivate_build:test-websocket-body-001 |
| T5 | Parallel | `parallel_context` in log, no pathfinder dispatch | none (coordinator direct) |
| T6 | Predictive | phase detected from verb distribution, predictions aligned | logged only |

All 6 test cases passed. Buffered build match detected in T4 before `create_build` is proposed. Log entries appended after each scan.
