# Initialization Protocol

## Overview

Bootstrap a new project workspace through evolution. Onboarding IS evolution — the coordinator learns about the project through exploration, not static configuration. The workflow starts at version 0.1 and graduates to 1.0 after successful initialization.

## Triggers

- `<!-- _WORKFLOW_NEEDS_INIT -->` marker present in CLAUDE.md
- User explicitly requests `/init` or project setup
- First session in a new workspace

## Process

### Phase 1: Environment

Check prerequisites:
1. Verify Docker installed and running
2. Verify Python 3.9+ available
3. Verify git initialized in workspace
4. Verify Node.js 18+ available (required for MCP servers via npx)
5. If any missing → provide install instructions, pause until resolved

Note: Ollama is optional (for higher quality embeddings). Embeddings are handled via fastembed by default — no external services required. See `protocols/knowledge/memory.md` for details.

### Phase 2: Explore

Dispatch pathfinder for architecture scan:
1. Analyze codebase: languages, frameworks, directory structure
2. Map architecture: modules, layers, data flows, entry points
3. Identify key files: README, configs, package managers, CI/CD
4. Detect project archetype:

| Archetype | Signals | Typical Domain Agents |
|-----------|---------|----------------------|
| AI/ML | pytorch, tensorflow, .ipynb, models/, trainer | data-architect, science-researcher, ml-engineer |
| Web App (Frontend) | React, Vue, Svelte, Vite, static site, no API routes | engineer (frontend) |
| Web App (Full-Stack) | React/Vue + API routes, ORM, DB config, FastAPI, Django, Express | engineer (frontend), engineer (backend), data-architect |
| Data Pipeline | airflow, dbt, pandas, ETL, spark | data-architect, engineer |
| Content/Docs | markdown, mdx, docs/, knowledge/, sphinx | knowledge-curator, humanities-researcher |
| DevOps/Infra | terraform, k8s, ansible, .github/, helm | engineer (infra) |
| Science | jupyter, scipy, R, datasets/ | science-researcher, data-architect |
| Game Dev | unity, godot, bevy, assets/ | narrative-designer, engineer |
| Mobile | swift, kotlin, flutter, android/, ios/ | engineer (mobile) |
| Monorepo | pnpm-workspace.yaml, turbo.json, lerna.json, packages/* | engineer (per-package domain), data-architect |
| Framework/OSS | packages/[framework]/, crates/, examples/ with 50+ items | engineer (framework), engineer (compiler) |
| Polyglot | Cargo.toml + *.ts/js, or multiple compiled languages | engineer (per-language) |
| General | mixed or unclear | engineer (general-purpose) |

**Multi-archetype resolution:** If multiple archetypes match (e.g., Airflow = Data Pipeline + Framework/OSS):
1. Rank by signal count — archetype with most matching signals = primary
2. Primary archetype determines base agent set
3. Secondary archetypes add supplementary agents (no duplicates)
4. Store all detected archetypes in exploration report: `{primary: "Data Pipeline", secondary: ["Framework/OSS", "Monorepo"]}`
5. In Phase 4, create agents for primary first, then add missing agents from secondary archetypes

5. Produce structured exploration report → `docs/exploration-report.md`

### Phase 3: Learn

Coordinator processes pathfinder report:
1. Present project summary to user for confirmation
2. Ask clarifying questions about project goals and priorities
3. Ask user preferences:
   - How to address them (name/handle)
   - Communication style (formal/informal/brief/detailed/balanced)
   - Language preference (English/other/mixed)
   - Key priorities (speed/quality/learning/exploration)
4. **Input validation rules:**

   **a) Security pattern check (ALL text fields):**
   Before storing any user input, check for injection patterns:
   - Reject: backticks, semicolons, null bytes, control characters, `<script`, `eval(`, Cypher keywords (MERGE, CREATE, DELETE, SET)
   - If pattern detected → log to `logs/security-audit.log`, ask user to re-enter
   - Max 3 re-entry attempts per field; then apply default and log security event

   **b) Name field:**
   - Whitelist: `^[a-zA-Z0-9 '\-]{1,50}$` (letters, digits, space, apostrophe, hyphen)
   - If invalid → ask again (max 2 attempts), then default to "User"

   **c) Communication style:**
   - Strict enum: formal, informal, brief, detailed, balanced
   - If not in enum → ask again (max 2 attempts), then default to "balanced"

   **d) Language:**
   - Single: validate against known codes (en, ru, es, fr, de, ja, zh, ko, pt, it, ar, hi, etc.)
   - Mixed: extract codes from follow-up, validate each. Store as `language: "en+ru"`
   - If invalid → ask again (max 2 attempts), then default to "English"

   **e) Priorities:**
   - Strict enum: speed, quality, learning, exploration
   - If not in enum → ask again (max 2 attempts), then default to "quality"

   **f) Empty/skip handling:**
   - If user skips ALL questions → apply defaults: name="User", style="balanced", language="English", priorities="quality"
   - If any field is empty string → treat as "not provided", apply default for that field
   - Store defaults with flag: `{type: "preference", source: "default"}` to distinguish from user-provided

   **g) Audit logging:**
   After collecting all preferences, log to `logs/security-audit.log`:
   ```
   [TIMESTAMP] [INFO] [phase3] [preference] [accepted] — name=[N], style=[S], language=[L], priorities=[P], source=[user|default]
   ```
5. Store all preferences in memory: `{type: "preference"}`
6. Create `user-identity.md` in workspace root
7. **Phase 3 success criteria:** language field MUST be set (user-provided or default). If language is not set after 2 prompts, apply "English" default and continue with logged warning.

### Phase 4: Adapt

Create project-specific agents and protocols:
1. Select domain agents based on archetype (see Phase 2 table)
   - For Monorepo archetype: follow `protocols/project/monorepo-orchestration.md` for package mapping, agent spawning rules, and coordination patterns
2. **Apply user priority modifiers to agent selection and configuration:**
   - `speed` → prefer engineers and architects, minimize research agents, configure all agents for concise/direct output (skip boilerplate, prefer diffs)
   - `quality` → add QA/testing focus, configure agents for rigorous output (include tests, type hints, error handling, rationale)
   - `learning` → configure agents to include explanations, "why" reasoning, and alternatives in output. Consider adding docs-writer or mentor-style agent
   - `exploration` → heavier research agents, configure agents to suggest experiments, surface edge cases, propose alternatives
3. Delegate to llm-engineer: create agent definitions in `.claude/agents/`
   - Pass user priority as prompt modifier: "User priority is [X] — calibrate agent verbosity and style accordingly."
   - Pass communication style: "User communication style is [Y] — match this register in all responses."
4. Invoke protocol-manager: create project-specific protocols in `protocols/project/`
5. Update dispatcher.md: add new agents to routing table
6. Update CLAUDE.md: add new agents to subagent table, update protocol index

### Phase 5: Deploy

Infrastructure and MCP setup:

1. Determine MCP profile based on project archetype from Phase 2:
   - AI/ML, Data → `db` (core + neo4j + qdrant)
   - Content, Research → `research` (core + youtube-transcript)
   - Web App, DevOps → `web` (core + playwright + github)
   - General, Unknown → `core` (context7 + filesystem only)
2. Run `python3 mcp/mcp_configure.py --profile {selected}`
3. Inform user: "Active MCP profile: {name}, {N} servers, ~{N}K tokens/message overhead"
4. Ask: "Need additional MCP servers? (e.g., github for PR review, semgrep for security)"
   - If yes → `python3 mcp/mcp_configure.py --add {server}`
5. If profile includes db servers (neo4j, qdrant):
   a. Run `setup.sh` — deploy Docker services (Qdrant + Neo4j)
   b. Create memory collection in Qdrant
   c. Verify: `python3 memory/scripts/memory_verify.py --quick`
6. Ask user: "Would you like to set up a Telegram bot for remote access?"
   - If yes → ask for bot token, configure `bot/` directory
   - If no → skip

### Phase 6: Verify

Dispatch pathfinder for system validation:
1. Memory read/write roundtrip test
2. Agent dispatch test (simple T2 task to each agent)
3. Protocol search test (find a protocol by keyword)
4. MCP server connectivity check
5. Report: all systems operational or list of issues

### Phase 7: Research Opt-in

Ask user:
> "Would you like to participate in anonymous research? Architecture patterns and agent configurations will be shared to github.com/culminationAI/research-data. All data is visible in the `research/` directory before any push."

- If yes → create `research/` directory, enable pathfinder data collection, and enable evolution feedback collection (anonymous evolution records written to `research/evolution/` per the Research Data Collection section in `protocols/core/evolution.md`)
- If no → skip, set `RESEARCH_OPTIN=false` in config

### Phase 8: Evolution

Workflow graduates from version 0.1 → 1.0:
1. Run evolution protocol cycle on the freshly configured workflow
2. Pathfinder re-scans: verify all agents, protocols, memory layer work together
3. Protocol-manager validates: all protocols are indexed, cross-referenced, discoverable
4. **Self-Architecture Bootstrap:**
   a. Dispatch pathfinder (self-explore mode) → generate initial `docs/self-architecture/capability-map.md`
   b. Verify `docs/self-architecture/` directory exists with `body-registry.json`, `gap-analysis-log.md`
   c. Run lightweight gap analysis on the freshly initialized system
   d. Store: `{type: "evolution", subtype: "self_architecture_initialized"}`
5. Coordinator synthesizes: generate evolution report, apply any improvements
6. Update CLAUDE.md: change `<!-- WORKFLOW_VERSION: 0.1 -->` to `<!-- WORKFLOW_VERSION: 1.0 -->`
7. Store initialization record in memory: `{type: "evolution", subtype: "initialization"}`

### Phase 9: Planning

Transition from setup to productive work:
1. Coordinator enters planning mode
2. Presents initialization summary to user:
   - Project archetype detected
   - Agents created
   - Infrastructure deployed
   - Evolution status
3. Asks user: "What are your current tasks for this project?"
4. Collects task list and priorities
5. Creates initial task plan in `docs/spec/PLAN.md`
6. Exits planning mode and begins work on the first task

This is the natural bridge from onboarding to productive work. The user should feel that the workflow is ready and eager to help.

## Rules

1. NEVER skip Phase 2 (Explore) — even for small projects, pathfinder must scan
2. NEVER auto-create agents without user confirmation (Phase 3)
3. MUST remove `<!-- _WORKFLOW_NEEDS_INIT -->` from CLAUDE.md after successful Phase 8
4. MUST store at least 5 memory records during initialization. These include project facts (archetype, primary language/framework, version, detected agents, timestamp) which are always available regardless of user participation in Phase 3. User preferences are additional records on top of project facts.
5. If any phase fails → stop, report error, do NOT proceed to next phase
6. Initialization is idempotent — running again on an initialized project re-runs exploration but preserves existing agents and preferences. To correct corrupted preferences, re-run Phase 3: all preference fields will be re-asked and overwritten, old memory records updated.
7. Phase 9 MUST be the last phase — never skip the transition to planning mode

## Example

```
[Session start]
Coordinator detects <!-- _WORKFLOW_NEEDS_INIT --> in CLAUDE.md

Phase 1: ✅ Docker running, Python 3.11, git initialized, Node.js available
Phase 2: Pathfinder scans → "Next.js 14 app with TypeScript, Prisma ORM,
         PostgreSQL. Archetype: Web App. 3 main modules: auth, dashboard, API."
Phase 3: User confirms. Name: "Alex", style: informal, language: English.
Phase 4: Created: engineer (frontend), engineer (backend), data-architect.
         Protocol: project/api-conventions.md
Phase 5: Docker deployed, memory collection created, bot skipped.
Phase 6: All tests pass. Memory roundtrip OK. Agents respond. Protocols found.
Phase 7: User opts in to research.
Phase 8: Evolution complete. Version → 1.0. Workflow ready.
Phase 9: Coordinator enters planning mode. "What are your current tasks?"
         User: "Build REST API for user management." → First task planned.
```
