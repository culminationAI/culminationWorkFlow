# Self-Evolution Protocol

## Overview

Meta-cognitive extension to the evolution protocol. Enables the coordinator to detect capability gaps proactively, create temporary architectural enhancements ("evolution bodies"), and manage their lifecycle.

Key distinction:
- `protocols/core/evolution.md` handles **REACTIVE** evolution — corrections, routing fixes, rule refinement
- This protocol handles **PROACTIVE** evolution — gap detection, capability extension, body lifecycle

Both share the security gate from `evolution.md` Step 8.

## Triggers

| Trigger | Action |
|---------|--------|
| Complex task arrives where coordinator detects insufficient capability | Deep gap analysis → decision fork |
| Pathfinder self-explore reveals capability gap | Phase 2 (Gap Analysis) |
| 2+ consecutive T4+ task failures in same domain | Deep gap analysis |
| User requests `/evolve` | Full pipeline from Phase 1 |
| Session-start lightweight gap scan finds unresolved gaps | Phase 2 (Gap Analysis) |

## Pipeline

### Phase 1: Explore (Self-Scan)

Dispatch pathfinder in self-explore mode:
1. Scan `.claude/agents/` — list all agents, their domains, MCP servers
2. Scan `protocols/` — list all protocols by category
3. Check `mcp/mcp_configure.py --status` — active profile and servers
4. Check memory: `python3 memory/scripts/memory_search.py "capability gap blocker" --limit 10`
5. Produce or refresh `docs/self-architecture/capability-map.md`

Output: structured capability map covering agents, protocols, MCP, memory state.

### Phase 2: Gap Analysis

Run deep gap analysis (`protocols/core/gap-analysis.md` — Deep Scan):
1. Decompose the triggering task into required domain capabilities
2. Score each capability across 5 dimensions (AGENT, PROTOCOL, MEMORY, MCP, KNOWLEDGE)
3. Classify each gap: KNOWLEDGE vs STRUCTURAL
4. Output: gap report with severity and recommendations, appended to `docs/self-architecture/gap-analysis-log.md`

### Phase 3: Decision Fork

```
IF all gaps == KNOWLEDGE:
  → Strengthen memory path (no body needed)
    1. Dispatch researcher/pathfinder for knowledge acquisition
    2. Store findings: {type: "evolution", subtype: "knowledge_acquisition"}
    3. Search memory to confirm gap closed (re-run lightweight scan)
    4. Proceed with original task

IF any gap == STRUCTURAL:
  → Evolution body path
    1. Present gap analysis summary to user
    2. User approves body creation
    3. Proceed to Phase 4
```

KNOWLEDGE path is always preferred. Do not propose body creation unless a STRUCTURAL gap is confirmed.

### Phase 4: Body Creation

Design body manifest, register it, create component files.

**4a. Design manifest:**

```json
{
  "id": "body-{YYYY-MM-DD}-{short-descriptor}",
  "created": "ISO8601",
  "why": "Gap description — why this body is needed",
  "what_task": "The specific task that prompted creation",
  "gap_analysis_ref": "timestamp of the triggering gap analysis entry",
  "state": "draft",
  "ttl_sessions": 10,
  "ttl_days": 14,
  "sessions_since_last_use": 0,
  "last_used": null,
  "activated_at": null,
  "deactivated_at": null,
  "smoke_test_results": null,
  "cherry_picked_from": null,
  "components": {
    "agents": [
      {"action": "create|modify", "path": ".claude/agents/{name}.md", "description": "..."}
    ],
    "protocols": [
      {"action": "create|modify", "path": "protocols/{dir}/{name}.md", "description": "..."}
    ],
    "claude_md_rules": [
      {
        "action": "add|modify",
        "section": "Subagents — Team",
        "rule_text": "| agent-name | description |",
        "original_text": null
      }
    ],
    "mcp_profile": {
      "action": "switch|add|none",
      "target_profile": null,
      "servers_to_add": []
    },
    "memory_records": [
      {
        "text": "...",
        "metadata": {"type": "evolution", "subtype": "body_context"}
      }
    ]
  },
  "rollback": {
    "agents_to_delete": [],
    "agents_to_restore": [{"path": "...", "backup_path": "..."}],
    "protocols_to_delete": [],
    "protocols_to_restore": [{"path": "...", "backup_path": "..."}],
    "claude_md_rules_to_remove": [],
    "claude_md_rules_to_restore": [{"section": "...", "original_text": "..."}],
    "mcp_profile_to_restore": null
  }
}
```

**4b. Register:** Append body manifest to `docs/self-architecture/body-registry.json`.

**4c. Create component files** (agent `.md`, protocol `.md`) in their normal locations. Set body state: `draft`.

**4d. Backup originals:** For modified files, save current content to `evolve/backup-{date}-{filename}` before any edits. Populate `rollback` fields.

### Phase 5: Body Activation (Security-Gated)

Security gate — imported from `evolution.md` Step 8. All three checks MUST pass:

**5a. Immutable Rule Check:**
Parse all target files for `<!-- IMMUTABLE -->` blocks. If any body component modifies content within an immutable block → **REJECT**. Log: `{type: "security", action: "body_rejected", reason: "immutable_block_violation", body_id: "..."}`.

**5b. Protected File Check:**
Body MUST NOT modify these files (only human edits allowed):
- `protocols/core/evolution.md`
- `protocols/quality/security-logging.md`
- `memory/scripts/research_validate.py`
- `memory/scripts/memory_write.py`

If body targets any protected file → **REJECT**. Log security event.

**5c. Security Weakening Check:**
If body proposes any of the following → **REJECT**:
- Removing or weakening a MUST/MUST NOT rule
- Disabling logging, validation, or security checks
- Expanding agent file access permissions
- Reducing input validation strictness

**5d. Apply (if all checks pass):**
1. Copy agent files to `.claude/agents/`
2. Copy protocol files to `protocols/`
3. Apply CLAUDE.md rule additions (subagent table, protocol index)
4. Switch MCP profile if needed: `python3 mcp/mcp_configure.py --profile {X}` or `--add {Y}`
5. Store body memory records
6. Add routing entries to `protocols/core/dispatcher.md`
7. Update body manifest: `state → active`, set `activated_at`

### Phase 6: Smoke Test

Run 2–3 targeted tests from `protocols/quality/testing.md` relevant to the body's domain.

**Pass threshold:** 2 of 3 tests must pass.

| Result | Action |
|--------|--------|
| Pass | Body remains active. Store: `{type: "evolution", subtype: "body_activated"}`. Update `smoke_test_results` in manifest. |
| Fail | Execute rollback (see Downgrade process). Body returns to `draft` or is deleted. |

### Phase 7: Lifecycle Management

**State machine:**
```
[DRAFT] --smoke pass--> [ACTIVE] --TTL / inactivity--> [BUFFERED] --30 days--> [ARCHIVED]
                            ^                                |
                            +------ reactivate on demand ----+
```

---

#### Downgrade (ACTIVE → BUFFERED)

**Triggers:**
- TTL expired: `sessions_since_last_use > ttl_sessions` OR `(now - last_used) > ttl_days`
- 5 consecutive sessions without using any body component
- User requests `/deactivate-body {id}`

**Process:**
1. Execute rollback: delete created agents/protocols; restore originals from backup
2. Remove CLAUDE.md entries (subagent table, protocol index)
3. Remove routing entries from `dispatcher.md`
4. Restore MCP profile if it was switched
5. Update manifest: `state → buffered`, set `deactivated_at`
6. Memory records remain (knowledge is permanent)
7. Store: `{type: "evolution", subtype: "body_deactivated", body_id: "..."}`

---

#### Reactivation (BUFFERED → ACTIVE)

**Triggers:**
- Gap analysis recommends `reactivate_body:{id}`
- User requests `/reactivate-body {id}`

**Process:**
1. Read manifest from `body-registry.json`
2. Verify component files exist; regenerate from manifest if missing
3. Re-apply all components (agents, protocols, CLAUDE.md, MCP, memory records)
4. Add routing entries to `dispatcher.md`
5. Reset TTL counters: `sessions_since_last_use → 0`, set new `activated_at`
6. Run smoke tests (Phase 6)
7. Store: `{type: "evolution", subtype: "body_reactivated", body_id: "..."}`

---

#### Archive (BUFFERED → ARCHIVED)

**Triggers:**
- 30 days in buffer without reactivation
- User explicitly archives the body

**Process:**
1. Delete component files (agents, protocols, backups)
2. Update manifest: `state → archived`
3. Keep manifest in `body-registry.json` — WHY/WHAT metadata preserved as institutional memory
4. Store: `{type: "evolution", subtype: "body_archived", body_id: "..."}`

---

#### Cherry-pick

When a buffered body has one useful component but full reactivation is overkill:
1. Read source body manifest, identify the needed component
2. Create a new body with only that component
3. Set `cherry_picked_from: "{source-body-id}"` in new manifest
4. New body goes through Phase 5–6 normally
5. Source body remains buffered

## TTL Tracking (Session Start)

At every session start, after the lightweight gap scan, coordinator checks `body-registry.json`:

```python
for body in bodies where state == "active":
    if (now - body.last_used) > body.ttl_days:
        trigger downgrade(body.id)
    elif body.sessions_since_last_use > body.ttl_sessions:
        trigger downgrade(body.id)
    elif body.ttl_days - (now - body.last_used) <= 2:
        warn: f"Body {body.id} TTL expiring in ≤2 days"
```

If `body-registry.json` is missing, skip silently and create it on next body creation.

## Rules

1. Max **2 active bodies** at once — prevents config explosion and context bloat
2. Security gate from `evolution.md` Step 8 applies to ALL body activations — no exceptions
3. Bodies MUST NOT modify protected files (same list as `evolution.md`)
4. Every body MUST have complete rollback instructions before activation
5. KNOWLEDGE path is always preferred over STRUCTURAL when both could work
6. Bodies buffered >30 days without reactivation are candidates for archival
7. Lightweight gap analysis at session start MUST complete in <30 seconds (no subagents)
8. Coordinator presents gap findings and body proposal to user before activation — never activate silently
9. Body manifest retains full WHY/WHAT even after archival
10. Memory records from bodies persist even after body deactivation — knowledge is permanent

## Integration

| System | Integration point |
|--------|------------------|
| **evolution.md** | Shares security gate (Step 8), storage format (Step 9), and trigger #4 (`/evolve` command) |
| **gap-analysis.md** | Phases 1–3 of this protocol run gap analysis. Buffered body check in gap-analysis feeds Phase 3 decision fork. |
| **dispatcher.md** | Gap-check pre-step before T1–T5 classification; body routing entries added at activation, removed at downgrade |
| **initialization.md** | Phase 8 bootstraps `docs/self-architecture/` directory and initial capability map |
| **testing.md** | Phase 6 (smoke test) uses Wave 5 tests T21–T23 for self-evolution validation |
| **memory.md** | New metadata subtypes: `body_context`, `body_activated`, `body_deactivated`, `body_reactivated`, `body_archived`, `knowledge_acquisition` |
| **CLAUDE.md** | Protocol index entry, session-start TTL check, subagent table updated at activation/downgrade |
