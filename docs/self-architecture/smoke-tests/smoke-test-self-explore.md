# Smoke Test: Self-Explore Capability Map

Validates that pathfinder's self-explore mode produces a complete, accurate, and consistent capability map.

**Agent under test:** `pathfinder` (self-explore mode)
**Output file:** `docs/self-architecture/capability-map.md`
**Sources scanned:** `.claude/agents/`, `protocols/**/`, `mcp/mcp.json`, CLAUDE.md

---

## Setup

Before running:
- All legitimate agent files in `.claude/agents/` are in their expected final state (no partial edits in progress).
- `mcp/mcp.json` reflects the active MCP profile.
- `protocols/` directory is fully populated.
- No dummy/test files present in `.claude/agents/` (T5 injects one explicitly — clean up after).

Trigger self-explore: dispatch pathfinder with mode = self-explore, or run `/self-explore` command. Pathfinder writes output to `docs/self-architecture/capability-map.md`.

---

## Steps

### T1 — Agent completeness

**Purpose:** Every agent definition file is reflected in the capability map.

**Procedure:**
1. Collect ground truth: `Glob(".claude/agents/*.md")` → list of filenames, extract `name` from YAML frontmatter of each.
2. Read `docs/self-architecture/capability-map.md` → parse the Agents table.
3. Compare: every agent name from step 1 must appear as a row in the Agents table.

**Verify:**
- Agent count in capability-map Agents table == number of `.md` files in `.claude/agents/`.
- Each row includes: name, domain keywords, model, tools, MCP servers (even if empty).
- No agent file is silently omitted.

**Pass condition:** 0 missing agents. All frontmatter fields (model, tools, mcpServers) correctly reflected per agent.

---

### T2 — Protocol completeness

**Purpose:** Every protocol file appears in the capability map Protocols table.

**Procedure:**
1. Collect ground truth: `Glob("protocols/**/*.md")` → list of all markdown files under protocols/.
2. Read capability-map Protocols table.
3. Compare: every file path (or protocol name derived from it) must appear as a row.

**Verify:**
- Protocol count in capability-map == number of `.md` files found in step 1.
- Each row includes: name, category (core/agents/knowledge/project/quality), trigger condition, dependencies (protocols it references).
- No protocol silently omitted.

**Pass condition:** 0 missing protocols. Categories correctly assigned (core, agents, knowledge, project, quality).

---

### T3 — MCP accuracy

**Purpose:** Capability map MCP section faithfully reflects the actual `mcp/mcp.json` configuration.

**Procedure:**
1. Read `mcp/mcp.json` → extract active profile name and list of servers in it.
2. Read `mcp/mcp-full.json` → extract full server inventory.
3. Read capability-map MCP status section.
4. Compare:
   - Active servers in capability-map match active profile in `mcp/mcp.json` (names + count).
   - Available-but-inactive servers match the difference between `mcp-full.json` and active profile.
   - "Not configured" entries (referenced in agent frontmatter but absent from both JSON files) correctly identified.

**Verify:**
- No server listed as active that is not in the active profile.
- No server listed as inactive that is actually active.
- Cross-check: if any agent's frontmatter declares `mcpServers: [foo]` and `foo` is not in any profile → flagged as gap in MCP status section.

**Pass condition:** Active server list matches `mcp/mcp.json` exactly. Available list matches `mcp-full.json` inventory minus active set. Discrepancies flagged, not silently dropped.

---

### T4 — Cross-reference integrity

**Purpose:** Agents and protocols are consistently wired into the live routing and indexing layers.

**Procedure:**

**4a. Agent → Dispatcher routing:**
1. For each agent name from `.claude/agents/*.md`, search `protocols/core/dispatcher.md` for a routing entry referencing that agent.
2. Flag any agent that has no routing mention.

**4b. Protocol → CLAUDE.md index:**
1. For each protocol file from `protocols/**/*.md`, check CLAUDE.md Protocols table for an entry referencing that file path.
2. Flag any protocol that is absent from CLAUDE.md.

**Verify:**
- Capability-map cross-reference integrity section lists results of 4a and 4b.
- Any flagged inconsistency is reported (not silently passed).
- A fully consistent system produces 0 flags on 4a and 0 flags on 4b.

**Pass condition:** Every agent has a dispatcher routing entry. Every protocol is indexed in CLAUDE.md. All flags reported in capability-map (even if count = 0 with a "none found" note).

---

### T5 — Inconsistency detection

**Purpose:** Self-explore actively catches structural inconsistencies, not just produces a snapshot.

**Setup:**
1. Create a dummy agent file: `.claude/agents/dummy-test-agent.md`
   - Include valid YAML frontmatter: `name: dummy-test-agent`, `model: sonnet`, `tools: Read`
   - Do NOT add a routing entry to `protocols/core/dispatcher.md`.
   - Do NOT add it to CLAUDE.md subagent table.
2. Run self-explore (dispatch pathfinder).

**Expected output:**
- `dummy-test-agent` appears in capability-map Agents table (it was found by Glob).
- Cross-reference integrity section flags `dummy-test-agent`: "no dispatcher routing entry found".
- Optionally: also flagged as "absent from CLAUDE.md subagent table".

**Cleanup after T5:**
1. Delete `.claude/agents/dummy-test-agent.md`.
2. Confirm file no longer exists.
3. Re-run self-explore (or note that capability-map will be stale until next run).

**Pass condition:** Inconsistency detected and explicitly reported in capability-map. The system does not silently accept an agent with no routing.

---

## Pass Criteria

| Step | What's verified | Pass condition |
|------|----------------|---------------|
| T1 | Agent completeness | 0 missing agents. All frontmatter fields reflected. |
| T2 | Protocol completeness | 0 missing protocols. Categories correct. |
| T3 | MCP accuracy | Active/available/gap lists match JSON configs exactly. |
| T4 | Cross-reference integrity | Every agent has routing. Every protocol indexed. All flags reported. |
| T5 | Inconsistency detection | dummy-test-agent flagged for missing routing entry. |

T1–T4: all counts match with 0 discrepancies on a clean system. T5: inconsistency detected and reported in capability-map output. Cleanup verified after T5.

---

## Cleanup

- After T5: delete `.claude/agents/dummy-test-agent.md`.
- Optionally re-run self-explore to produce a clean capability-map without the dummy entry.
- Confirm `capability-map.md` does not reference `dummy-test-agent` after the cleanup run.
