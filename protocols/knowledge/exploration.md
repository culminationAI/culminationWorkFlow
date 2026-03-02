# Exploration Protocol

## Overview

Pathfinder's operational protocol for systematic project exploration and knowledge extraction. Replaces the mining protocol with a broader scope: architecture analysis, knowledge extraction, memory maintenance, post-change verification, and web research.

## Triggers

- Initialization Phase 2 (architecture scan)
- Coordinator dispatches pathfinder for any exploration task
- User request: `/explore [topic]`
- Post-refactor: coordinator requests re-scan
- Periodic: memory maintenance schedule

## Modes

### 1. Architecture Scan

Full codebase analysis → structured report.

1. **Discover** — Glob for key files:
   - Package managers: `package.json`, `Cargo.toml`, `pyproject.toml`, `go.mod`, `Gemfile`, `pom.xml`
   - Configs: `tsconfig.json`, `.eslintrc*`, `docker-compose*`, `Makefile`, `.env*`
   - CI/CD: `.github/workflows/*`, `.gitlab-ci.yml`, `Jenkinsfile`
   - Docs: `README*`, `docs/`, `CHANGELOG*`
2. **Analyze** — Read entry points, map imports, identify patterns
3. **Classify** — Determine project archetype (see initialization protocol)
4. **Report** — Write structured report to `docs/exploration-report.md`:
   - Stack: languages, frameworks, versions
   - Architecture: pattern, layers, modules
   - Dependencies: external packages, internal modules
   - Key files: entry points, configs, documentation
   - Recommendations: suggested agents, potential improvements

### 2. Knowledge Extraction

Structured data from docs/code → memory (Qdrant + Neo4j).

1. **Identify sources** — find documentation, comments, README files
2. **Extract facts** — parse structured information (APIs, schemas, rules)
3. **Validate** — cross-reference facts with code
4. **Store** — write to memory via `memory/scripts/memory_write.py`:
   - One fact per record, max 200 tokens
   - Set appropriate metadata: `{type: "decision|pattern|architecture"}`
   - Check for duplicates before writing

### 3. Memory Maintenance

Verify, validate, deduplicate, clean up.

1. **Health check** — `python3 memory/scripts/memory_verify.py --quick`
2. **Duplicate scan** — `python3 memory/scripts/memory_dedupe.py --dry-run`
3. **Stale detection** — search for records referencing deleted/moved files
4. **Garbage detection** — find records <15 chars or matching known garbage patterns
5. **Cleanup** — with coordinator approval: `python3 memory/scripts/memory_cleanup.py --execute`
6. **Report** — maintenance summary: records checked, dupes found, stale flagged, garbage removed

### 4. Post-Change Verification

Re-scan after major changes.

1. **Get diff** — list of changed/added/deleted files (from coordinator or git)
2. **Search memory** — find records referencing changed files
3. **Re-read** — read changed files, compare with memory records
4. **Update** — fix stale records, remove records for deleted files
5. **Flag** — report inconsistencies between docs and implementation
6. **Verify docs** — check if documentation still matches current state

### 5. Web Research

Find external information for project analysis.

1. **Identify unknowns** — frameworks, libraries, patterns not in memory
2. **Search** — WebSearch for documentation, best practices
3. **Summarize** — extract relevant information
4. **Store** — write findings to memory with `{type: "reference"}`

## Process (General)

```
Task received from coordinator
    ↓
Select mode based on task description
    ↓
Execute mode steps
    ↓
Produce structured report
    ↓
Return JSON-summary to coordinator
```

## Rules

1. Always produce structured output (reports with sections, not free prose)
2. Never modify source code — only memory records, reports, documentation
3. Use `--dry-run` before any destructive memory operations
4. One fact per memory record, max 200 tokens, English only
5. Cross-reference findings with file paths and line numbers
6. For web research: always cite sources
7. Memory scripts are in `memory/scripts/` — use them, don't call APIs directly
8. If unsure about a finding, flag it as "unverified" in the report

## Example

```
Task: "Architecture scan for new Rails project"
Mode: Architecture Scan

1. Glob → Gemfile, config/routes.rb, app/, db/migrate/
2. Read Gemfile → Rails 7.1, PostgreSQL, Sidekiq, Devise
3. Read routes.rb → 15 controllers, REST API + web views
4. Classify → Web App archetype, MVC pattern
5. Report:
   Stack: Ruby 3.2, Rails 7.1, PostgreSQL, Redis/Sidekiq
   Architecture: MVC, 15 controllers, 3 namespaces (admin, api, web)
   Agents: engineer (backend), data-architect (PostgreSQL)
   Key files: config/routes.rb, app/models/, db/schema.rb
```
