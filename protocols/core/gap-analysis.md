# Gap Analysis Protocol

## Overview

Permanent analysis capability. Detects gaps between what a task requires and what the system can currently deliver. Runs at two intensities:

- **Lightweight** — every session start, no subagent dispatch, ~30 seconds
- **Deep** — triggered by complex tasks or explicitly requested, dispatches pathfinder in self-explore mode

Results are logged to `docs/self-architecture/gap-analysis-log.md` and stored in memory after every scan.

## Triggers

| Trigger | Intensity |
|---------|-----------|
| Session start (step 5, after memory load) | Lightweight |
| Coordinator detects task exceeding current capability | Deep |
| User requests `/gap-analysis` | Deep |
| 2+ consecutive T4+ task failures in same domain | Deep |

## Lightweight Scan

No subagents. Reads three sources, produces one paragraph.

**Steps:**
1. Read `docs/self-architecture/capability-map.md`
   - If missing → skip, schedule a deep scan for next opportunity
2. Read `docs/self-architecture/body-registry.json` — check active body TTLs for expiry warnings
3. Search memory: `"gap analysis blocker capability"` `--limit 5`
4. Output: 1-paragraph status — one of:
   - No gaps detected since last analysis
   - N gaps found in last deep scan (list domains)
   - Body TTL warnings (list expiring bodies)

## Deep Scan

Dispatches pathfinder. Produces scored gap report.

### Step 1: Explore

Dispatch pathfinder in self-explore mode → produce or refresh `docs/self-architecture/capability-map.md`.

### Step 2: Decompose

Break the task into a list of domain capabilities required. Each capability becomes a scored requirement.

### Step 3: Score

Score each requirement across 5 dimensions (0.0–1.0):

| Dimension | What it checks | 1.0 | 0.5 | 0.0 |
|-----------|---------------|-----|-----|-----|
| `AGENT_COVERAGE` | Agent in `.claude/agents/` covers this domain | covered | partial | missing |
| `PROTOCOL_COVERAGE` | Protocol in `protocols/` guides this workflow | exists | partial | missing |
| `MEMORY_COVERAGE` | Memory has relevant context (search by keywords) | >5 results | 1–5 results | empty |
| `MCP_COVERAGE` | Required tools available in active MCP profile | active | in full profile | not configured |
| `KNOWLEDGE_COVERAGE` | System knows enough about domain (memory + `docs/tech/`) | sufficient | partial | insufficient |

### Step 4: Aggregate

- Per-requirement score = average of its 5 dimension scores
- Overall gap score = average of all per-requirement scores

## Thresholds

| Overall score | Interpretation |
|--------------|----------------|
| > 0.8 | No structural gap — knowledge strengthening may help |
| 0.5–0.8 | Partial gap — evolution body recommended |
| < 0.5 | Significant gap — evolution body required |

## Gap Classification

Two gap types, detected per requirement:

**KNOWLEDGE gap** — MEMORY or KNOWLEDGE < 0.5, but AGENT + PROTOCOL + MCP all >= 0.5
→ Action: strengthen memory (dispatch researchers, web search, extract knowledge). Do NOT create a body.

**STRUCTURAL gap** — AGENT or PROTOCOL or MCP < 0.5
→ Action: create evolution body (see `protocols/core/self-evolution.md`). Check buffered bodies first.

## Buffered Body Check

Before recommending body creation, check `body-registry.json` for buffered bodies:

1. Match gap against each buffered body's `what_task` field
2. Match gap against `components.agents[].description` in each buffered body
3. If match found → recommend **reactivation** of that body (provide body ID)
4. Reactivation is always preferred over creating a new body

## Severity Mapping

Computed per requirement from its average score:

| Avg score | Severity | Meaning |
|-----------|----------|---------|
| >= 0.8 | none | No action needed |
| 0.6 – 0.8 | low | Can probably work around it |
| 0.4 – 0.6 | medium | Body recommended |
| 0.2 – 0.4 | high | Body required |
| < 0.2 | critical | Multiple fundamental capabilities missing |

## Output Format

After every scan, append a JSON entry to `docs/self-architecture/gap-analysis-log.md`:

```json
{
  "scan_type": "lightweight|deep",
  "timestamp": "ISO8601",
  "overall_score": 0.72,
  "gaps": [
    {
      "requirement": "description of what's needed",
      "scores": {
        "agent": 1.0,
        "protocol": 0.5,
        "memory": 0.0,
        "mcp": 1.0,
        "knowledge": 0.5
      },
      "classification": "KNOWLEDGE|STRUCTURAL",
      "severity": "low|medium|high|critical",
      "recommendation": "strengthen_memory|create_body|reactivate_body:{id}"
    }
  ],
  "active_bodies": ["body-id"],
  "buffered_bodies_relevant": ["body-id"]
}
```

Lightweight scan entries omit `gaps` array (no per-requirement analysis). They include only `scan_type`, `timestamp`, `overall_score` (from last deep scan), and a `status` string.

## Rules

1. Lightweight scan MUST NOT dispatch subagents — too expensive at session start
2. Deep scan dispatches pathfinder (self-explore mode) ONLY — no other subagents
3. Gap analysis results stored in memory: `{type: "gap_analysis"}` after every scan
4. If a buffered body matches the gap, recommend reactivation — never recommend body creation first
5. Never recommend body creation for KNOWLEDGE-only gaps — strengthen memory instead
6. Log entry appended after EVERY scan (lightweight or deep)
7. Coordinator presents gap findings to user before proceeding with body creation
8. `capability-map.md` missing = schedule deep scan, do NOT block session start

## Integration

| System | Integration point |
|--------|------------------|
| **Dispatcher** | Before T1–T5 classification, check if domain coverage is known low. If so, upgrade task tier or flag gap. |
| **Self-Evolution** | Deep gap analysis is Phase 2 of the self-evolution pipeline. |
| **Session Start** | Lightweight scan is step 5 of coordinator's session start flow (after memory load). |
| **Memory** | All gap analysis results stored with `{type: "gap_analysis"}` metadata. |
