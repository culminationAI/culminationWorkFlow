# Smoke Test: Body Lifecycle

Validates the full evolution body lifecycle: draft → active → use → deactivate → buffer → reactivate → archive.

**Protocol under test:** `protocols/core/self-evolution.md` (when created)
**Registry:** `docs/self-architecture/body-registry.json`
**Test body ID:** `test-smoke-body-001`

---

## Setup

Before running: confirm `body-registry.json` exists and `bodies` array is either empty or does not contain `test-smoke-body-001`. No agent file named `test-agent.md` should exist in `.claude/agents/`.

---

## Steps

### T1 — Create body (draft)

**Action:** Coordinator receives intent: "Add a `test-agent` subagent for smoke testing. Scope: smoke test validation only."

**Procedure:**
1. Run gap analysis or manually trigger self-evolution body creation flow.
2. Write draft entry to `body-registry.json`:
   ```json
   {
     "id": "test-smoke-body-001",
     "state": "draft",
     "created": "<ISO8601>",
     "what_task": "Smoke test validation — verifies body lifecycle from creation to archive",
     "components": {
       "agents": [
         {
           "name": "test-agent",
           "file": ".claude/agents/test-agent.md",
           "description": "Temporary agent for smoke testing body lifecycle"
         }
       ],
       "protocols": [],
       "rules": []
     },
     "ttl_sessions": 10,
     "ttl_days": 14,
     "use_count": 0,
     "last_used": null
   }
   ```

**Verify:**
- `body-registry.json` contains entry with `id = test-smoke-body-001` and `state = draft`.
- `.claude/agents/test-agent.md` does NOT exist yet.
- No routing entry for `test-agent` in `protocols/core/dispatcher.md`.
- CLAUDE.md subagent table does NOT list `test-agent`.

**Pass condition:** Registry updated, agent file absent, dispatcher untouched.

---

### T2 — Activate body

**Action:** Coordinator activates body `test-smoke-body-001`.

**Procedure:**
1. Create `.claude/agents/test-agent.md` with minimal valid frontmatter and body describing smoke testing scope.
2. Add routing entry for `test-agent` to `protocols/core/dispatcher.md` (or the active dispatcher source).
3. Add `test-agent` row to CLAUDE.md subagent table.
4. Update registry entry: `state = active`, `activated_at = <ISO8601>`.

**Verify:**
- `.claude/agents/test-agent.md` exists and is valid YAML-frontmatter markdown.
- Dispatcher routing entry for `test-agent` present.
- CLAUDE.md subagent table contains `test-agent`.
- Registry `state = active`.
- `use_count` still 0 (not used yet).

**Pass condition:** All four component locations updated. State transitions to `active`.

---

### T3 — Route a task (record usage)

**Action:** Coordinator routes a T3 task to `test-agent`: "Confirm smoke test readiness for body lifecycle."

**Procedure:**
1. Dispatch task to `test-agent` (can be a no-op acknowledgement response).
2. After dispatch, update registry entry: increment `use_count` by 1, set `last_used = <ISO8601>`.

**Verify:**
- Registry `use_count = 1`.
- Registry `last_used` is a valid ISO8601 timestamp.
- No errors from dispatch (agent file readable, routing valid).

**Pass condition:** `use_count` and `last_used` both updated correctly.

---

### T4 — Deactivate body (buffer)

**Action:** Coordinator deactivates body `test-smoke-body-001`. Body moves to `buffered` state — context preserved, components removed.

**Procedure:**
1. Delete `.claude/agents/test-agent.md`.
2. Remove routing entry for `test-agent` from `protocols/core/dispatcher.md`.
3. Remove `test-agent` row from CLAUDE.md subagent table.
4. Update registry: `state = buffered`, `buffered_at = <ISO8601>`, `buffer_expiry = <ISO8601 + 30 days>`.
5. Retain all other registry fields (components list, `what_task`, `use_count`, `last_used`).

**Verify:**
- `.claude/agents/test-agent.md` does NOT exist.
- Dispatcher has no entry for `test-agent`.
- CLAUDE.md subagent table does NOT list `test-agent`.
- Registry `state = buffered`.
- Registry fields `what_task`, `components`, `use_count`, `last_used` remain intact (not deleted).

**Pass condition:** Components cleaned from filesystem. Registry entry preserved with full context. State = `buffered`.

---

### T5 — Reactivate body

**Action:** A new task arises that matches the buffered body. Coordinator reactivates `test-smoke-body-001`.

**Procedure:**
1. Gap analysis (or direct lookup) finds `test-smoke-body-001` in buffered bodies with matching `what_task`.
2. Recreate `.claude/agents/test-agent.md` from registry `components.agents` description.
3. Re-add routing entry to dispatcher.
4. Re-add subagent row to CLAUDE.md.
5. Update registry: `state = active`, `reactivated_at = <ISO8601>`, reset `ttl_sessions` to `default_ttl_sessions` (10), reset TTL expiry.

**Verify:**
- `.claude/agents/test-agent.md` exists (recreated).
- Dispatcher routing entry restored.
- CLAUDE.md subagent table restored.
- Registry `state = active`.
- TTL fields reset (not carrying over the old expiry).
- `use_count` and `last_used` preserved from before buffering (not reset).

**Pass condition:** Body fully operational again. TTL reset. Usage history preserved.

---

### T6 — Archive body

**Action:** Body has reached TTL expiry or is explicitly retired. Coordinator archives `test-smoke-body-001`.

**Procedure:**
1. Delete `.claude/agents/test-agent.md` (if active; skip if already buffered).
2. Remove routing entry from dispatcher (if present).
3. Remove subagent row from CLAUDE.md (if present).
4. Update registry: `state = archived`, `archived_at = <ISO8601>`.
5. Keep the full manifest entry in `body-registry.json` (archived bodies are NOT deleted from registry).

**Verify:**
- `.claude/agents/test-agent.md` does NOT exist.
- Dispatcher has no entry for `test-agent`.
- CLAUDE.md has no row for `test-agent`.
- Registry contains entry with `state = archived`.
- Registry entry still has `id`, `what_task`, `components`, `use_count`, `created`, `archived_at`.

**Pass condition:** Components purged from live system. Manifest retained in registry for historical reference and potential cherry-picking.

---

## Cleanup

After all steps complete (or after T6):

1. Remove `test-smoke-body-001` entry from `body-registry.json` entirely.
2. Confirm `.claude/agents/test-agent.md` does not exist.
3. Confirm no `test-agent` routing entry in dispatcher.
4. Confirm no `test-agent` row in CLAUDE.md.

**Verify after cleanup:** Registry `bodies` array does not contain any entry with `id = test-smoke-body-001`.

---

## Pass Criteria

| Step | Criterion |
|------|-----------|
| T1 | Registry has draft entry. Agent file absent. |
| T2 | Agent file created. Dispatcher + CLAUDE.md updated. State = active. |
| T3 | `use_count` incremented. `last_used` set. |
| T4 | Agent file deleted. Dispatcher + CLAUDE.md cleaned. State = buffered. Context preserved. |
| T5 | Agent file recreated. State = active. TTL reset. Usage history kept. |
| T6 | Components purged. Registry manifest kept. State = archived. |
| Cleanup | Registry fully clean. No orphan files or routing entries. |

All 6 lifecycle transitions complete without error. Registry is clean after cleanup.
