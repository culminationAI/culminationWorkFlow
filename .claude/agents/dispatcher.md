# Dispatcher — Coordinator Reference

> Not a subagent. The coordinator applies these rules mentally on every request.

## Request Classification (by verb)

| Verb | Tier | Steps | Output |
|------|------|-------|--------|
| show, find, open | T1 | 1 | <500 tok |
| add, edit, fix | T2 | 2-3 | <2K tok |
| write, create, analyze | T3 | 4-8 | 2-5K tok |
| design, architect, debug | T4 | 8-20 | 5-15K tok |
| research, prove, compare 5+ sources | T5 | 20+ | 15K+ tok |

## Model and Thinking

| Tier | Model | Thinking |
|------|-------|----------|
| T1 | haiku | off |
| T2 | sonnet | off |
| T3 | sonnet | effort: medium |
| T4 | opus | effort: high |
| T5 | opus | effort: max |

## Routing

| Tier | Delegate to |
|------|-------------|
| T1 | **Direct tool** (Grep, Glob, Read) — NEVER use subagents for T1. Subagents load 30K+ baseline context, wasting 100x tokens vs direct tool (~500 tok). |
| T2 | general-purpose (sonnet) |
| T3+ | Specialized subagent by domain |

### Base agents (always available)

| Domain | Subagent |
|--------|----------|
| Python, Docker, API, scripts, tests, infrastructure | engineer |
| Prompt design, context engineering, model routing, LLM debugging, agent creation | llm-engineer |

### Domain agents (created during initialization)

Domain agents are added during initialization via the agent-creation protocol (`protocols/agent-creation.md`).
Each project defines its own domain agents based on the knowledge areas it covers.

> When routing, check `.claude/agents/` for available domain agents beyond the base two.

## Prompt Checklist

Before delegating to a subagent — verify the prompt includes:

- [ ] **What to do** — one sentence, task core
- [ ] **Scope out** — what is NOT part of the task
- [ ] **Format** — markdown/JSON/text, structure
- [ ] **Length** — max_length in tokens
- [ ] **Language** — English for prompts
- [ ] **File path (VALIDATED)** — if result must be written to a file, **MUST run Glob to verify the path exists** before dispatching. Never assume file names from memory — always check filesystem.
- [ ] **Context** — minimally necessary (don't overload)
- [ ] **Memory context** — search memory by task, include relevant context in prompt
- [ ] **Protocol context** — search memory for relevant protocols, inject key rules into prompt
- [ ] **Contract version** — if task depends on a contract, verify it's current
- [ ] **Executor lock** — verify no other subagent is working on the same files
- [ ] **Parallel context** — if running parallel tasks, inject brief summary of sibling tasks (see § Parallel Task Protocol)

## Contract Handoffs Between Subagents

When subagent A creates an artifact for subagent B — pass `report_file` explicitly in B's prompt, don't retell contents:

| Junction | What to pass |
|----------|-------------|
| domain-agent → data-architect | `report_file` Semantic Model |
| data-architect → engineer | `report_file` Data Spec |
| engineer → domain-agent | `report_file` Implementation Report |
| domain-agent → llm-engineer | `report_file` Agent Spec (what agent should know) |
| llm-engineer → engineer | `report_file` Prompt Spec (optimized system prompt) |
| researcher → knowledge-curator | list of `files_changed` |

**Prompt format:** "Use the Data Spec from `path/to/spec.md` (created by data-architect)" — subagent reads the file itself.

## Post-Dispatch Verification

After EVERY subagent completes:

1. **Check `files_changed`** — verify each file exists using Glob. If missing → agent silently failed, retry or escalate.
2. **Check `report_file`** — if non-null, verify file exists. If null but agent should have written output → flag as contract violation.
3. **Store to memory** — search memory for key phrase → check duplicates → write to memory with metadata `{type, agent_id}`. This is MANDATORY, not optional.
4. **Log decision** — if the subagent made a design decision worth preserving, store it as `{type: "decision"}`.

## Parallel Task Protocol

When running 2+ subagents in parallel on related topics:

1. **Before dispatch**: include in EACH agent's prompt a 1-2 sentence summary of what sibling agents are working on:
   ```
   Note: In parallel, [agent-A] is covering [topic X] and [agent-B] is covering [topic Y].
   Include cross-references to their output files in your "Related Documents" section.
   ```
2. **Sibling file paths**: provide the output file paths of ALL parallel agents, so each can add cross-references.
3. **After all complete**: coordinator writes a synthesis document linking all parallel outputs (for T4+ tasks).

## Rules

1. **Classify by the REQUEST VERB**, not by file state
2. **When in doubt** between adjacent tiers — choose lower, escalate if needed
3. **Coordinator never executes domain tasks directly** — only routes and synthesizes
4. **Max subagents:** 2 for T3, 3 for T4, unlimited for T5
5. **Start response with `[T{n}]`** so the user sees the classification
6. **Respond to user in the project language** (set in CLAUDE.md)
7. **Scoped handoffs** — each subagent gets only file paths + task description, not full conversation history
8. **T1 = direct tool** — never delegate T1 to subagent. If one Grep/Glob/Read can answer it, use it directly.
9. **Validate paths before dispatch** — run Glob to confirm file existence. Never construct paths from memory.
10. **Coordinator NEVER writes files** — if the task creates or modifies a file (code, scripts, docs, configs), it MUST be delegated to a subagent. Coordinator only writes plan files and memory records.
