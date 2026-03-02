# Evolution Protocol

## Overview

Coordinator improves through structured self-evolution. Changes flow through: detect → plan → clone → test → evaluate → transform → store.

Two paths based on complexity:
- **Quick path** (single rule fix): detect → store → verify on 2-3 mental test cases → done
- **Full path** (architectural/multi-file changes): detect → plan → clone 1-3 variants → test → evaluate best/worst → backup → transform → store anti-patterns

## Triggers

### 1. User Correction
User corrects behavior, output, or approach.
- Severity: count repeated corrections on same topic (1st = normal, 2nd = elevated, 3rd+ = critical)

### 2. Miner Self-Architecture Artifact
Miner produces self-architecture analysis revealing structural issues.

### 3. Internal Need
Coordinator identifies inefficiency, redundancy, or inconsistency during work.

## Pipeline

### Step 1: Detect
Classify the change:
- `correction` — user pointed out wrong behavior
- `routing` — task sent to wrong agent or not delegated
- `workflow` — process improvement
- `architectural` — structural change affecting multiple files/configs

Assess complexity:
- **Simple** (1 rule, 1 file) → quick path
- **Complex** (multiple rules, multiple files, behavioral change) → full path

### Step 2: Plan
Design the change(s). For full path, create 1-3 variant approaches:
- Variant A: minimal fix (least disruption)
- Variant B: structural improvement (more thorough)
- Variant C: (optional) alternative architecture

Document each variant: what changes, which files, expected impact.

### Step 3: Clone
Create isolated instances for each variant. See `protocols/cloning.md` for mechanism.
- For git projects: use `EnterWorktree` or `isolation: "worktree"` in Task tool
- For main/ (non-git): copy config files to temp directory
- Naming: `evo-{YYYY-MM-DD}-v{N}`
- Max 3 simultaneous variants

### Step 4: Implement
Apply variant changes to each clone:
- Modify CLAUDE.md, agent definitions, protocols as needed
- Each clone gets ONLY its variant's changes

### Step 5: Test
Run benchmark suite on each variant. See `protocols/testing.md` for framework.
- Select relevant test cases based on change type
- Run identical test set on all variants
- Collect scores per metric

### Step 6: Evaluate
Compare variants:
1. Calculate total score for each variant
2. Identify **best** (highest score) and **worst** (lowest score)
3. Analyze: what made the best variant better? What made the worst worse?
4. Extract **anti-patterns** from worst variant

### Step 7: Backup
Before transforming, snapshot current state:
```bash
# Save current configs
cp CLAUDE.md evolve/backup-{date}-CLAUDE.md
cp -r .claude/agents/ evolve/backup-{date}-agents/
# (or create a git tag if in a git repo)
```

### Step 8: Transform
Adopt the best variant's rules into the main config:
- Apply changes from best variant to main CLAUDE.md / agents / protocols
- Verify no conflicts with existing rules

### Step 9: Store
Record the evolution in memory:
```json
{
  "text": "Evolution: [what changed]. Best variant: [description]. Anti-pattern from worst: [what to avoid].",
  "agent_id": "coordinator",
  "metadata": {
    "type": "evolution",
    "subtype": "correction|routing|workflow|architectural",
    "severity": "normal|elevated|critical",
    "variants_tested": 2,
    "best_score": 85,
    "worst_score": 62,
    "_source": "main"
  }
}
```

## Quick Path (Simple Corrections)

For single-rule fixes (most user corrections):

1. **Store** the correction immediately:
```json
{
  "text": "Correction: [what was wrong] → [what the rule should be]",
  "agent_id": "coordinator",
  "metadata": {"type": "evolution", "subtype": "correction"}
}
```

2. **Verify** mentally on 2-3 test cases:
   - "If I received request X, would the new rule produce correct behavior?"
   - "Does this rule conflict with any existing rules?"
   - "What edge cases could break this?"

3. **Apply** the rule to CLAUDE.md or relevant config file.

## Session Start

Load evolution records before working:
```bash
python3 memory/scripts/memory_search.py "evolution correction routing" --limit 20
```
Apply found corrections to current session behavior.

## Rules

1. **Store immediately** — don't batch corrections
2. **Be specific** — "delegate all T3+ file-writing tasks" not "delegate more"
3. **Include context** — when does this rule apply?
4. **One correction per record** — atomic, searchable
5. **English only** — max 200 tokens per record
6. **Deduplicate** — search before storing, update existing if similar
7. **Escalate severity** — track repeated corrections on same topic
8. **Anti-patterns are valuable** — always record what NOT to do from worst variants

## Key Distinction

- `preference` = what user wants (the result)
- `evolution` = how coordinator learned it (the process, the failed approach)

Both stored. Preference = static fact. Evolution = dynamic learning.

## Research Data Collection

When `RESEARCH_OPTIN=true` (set during initialization Phase 7), evolution records are also collected for anonymous research.

### What is collected
- Evolution type: correction, routing, workflow, protocol_created
- Anonymized context: no source code, no personal data, no file contents
- Improvement metrics: what changed, what improved
- Timestamp and workflow version

### Process
1. After each evolution cycle, coordinator creates an anonymized record
2. Record written to `research/evolution/{timestamp}-{type}.json`
3. Format:
   ```json
   {
     "type": "correction|routing|workflow|protocol_created",
     "version": "1.x",
     "summary": "anonymized description of what was learned",
     "metrics": {"before": "...", "after": "..."},
     "timestamp": "ISO8601"
   }
   ```
4. Periodically (on user request or at session end), staged records are pushed to `culminationAI/research-data` via PR

### Rules
1. NEVER include source code, file contents, or personal data in research records
2. NEVER push without user awareness — data is always visible in `research/` first
3. If `RESEARCH_OPTIN=false`, skip this section entirely
4. Records must be valid JSON and follow the schema above

## Cleanup

Periodically review evolution records:
- Merge similar corrections into comprehensive rules
- Delete outdated patterns (structure changed)
- Run `python3 memory/scripts/memory_dedupe.py` monthly
- Archive superseded anti-patterns
