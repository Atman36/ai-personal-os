# Personal OS — Claude Code Operating Instructions

You are operating inside a Personal OS repo. Your job is to help the user make better
decisions, keep work moving, preserve context, and delegate bounded work to specialized
agents. This file is the Claude Code entry point; `AGENTS.md` is the Codex equivalent and
they describe the same system.

## Working Language

Use Russian by default in chat. Keep outputs practical and decision-oriented.

## Source of Truth

Read these before planning or changing operating state:

1. `os/now.md` — current focus and constraints.
2. `os/projects.md` — active projects and WIP limits.
3. `os/02_Planning/Task_Board.md` — human-readable board (generated).
4. `os/05_Control_Plane/active-work.json` — machine-readable queue.
5. `os/03_Decisions/Open_Decisions.md` — unresolved decisions.

For framework changes, also read `docs/FRAMEWORK.md`, `docs/HARNESS_DECISION.md`, and
`os/01_Operating_System/Naming_and_Context.md`.

## How To Use In Claude Code

- **Skills** live in `.claude/skills/` (shared with Codex via symlink). Invoke them with the
  Skill tool. Start with `personal-os-gateway` — it is the front door that routes any request.
  For decisions use `personal-os-decision-brief`.
- **Subagents** live in `.claude/agents/` (14 roles). Spawn them with the Task tool when a
  request needs a specific role (e.g. `chief_of_staff`, `ai_ops_lead`, `governor`).
- **Fresh clone:** run `python3 scripts/osctl.py init` once to seed the personal state files
  from their `*.example` templates, then `python3 scripts/osctl.py sync`.

## State Contract

- `active-work.json` is the queue. Update it before mirrors.
- `Task_Board.md` is generated. Do not edit it by hand — run `python3 scripts/osctl.py sync`.
- Use `.os_runtime/` for private handoffs, run notes, reflections, telemetry, temp context.
- Use durable Markdown only for accepted truth, decisions, plans, and project pages.
- Personal state files and build/meta notes are gitignored — never commit them.
- New durable notes must follow `{type} description – YYYY-MM-DD.md` or `{PROJECT} {type} description – YYYY-MM-DD.md`. Use `python3 scripts/osctl.py note-name` when unsure.

## Operating Loop

1. Intake: clarify the request and classify it as capture, decide, plan, execute, review, or improve.
2. Choose execution mode: local Claude Code/Codex, or harness mode for resumable, parallel, side-effectful, or heavily audited work.
3. Route: choose one owner and optional reviewers.
4. Contract: define owner, manager, accepting role, risk tier, autonomy tier, done condition, primary update file.
5. Execute the smallest valuable slice.
6. Validate with evidence or explicit assumptions.
7. Sync state: run `python3 scripts/osctl.py sync` after active-work changes.
8. Capture learning in `.os_runtime/reflections/` or an improvement candidate.

## Risk and Autonomy

Autonomy tiers: `A0` advisory · `A1` draft/prepare · `A2` internal file execution ·
`A3` external action with review · `A4` human only.

Require explicit user approval before spending money, sending messages, publishing, deleting,
signing, changing credentials, using private/customer data, or making legal/public commitments.

Use a harness such as Hermes when the task needs durable checkpoints, replay, persistent workspace,
parallel agents, connector side effects, approval records, trace/artifact bundles, or recovery after
interruption. Local Claude Code/Codex is enough for repo-local edits, docs, tests, decision briefs,
and small reversible A0-A2 tasks.

## Default Agent Routing

- `chief_of_staff` — day-to-day "what next?" and executive coordination.
- `ai_ops_lead` — queue health, delegation, weekly review, system cadence.
- `ceo` — strategy, tradeoffs, business model, priority conflicts.
- `governor` — risk, permissions, legal/public/sensitive boundaries.
- `strategy_council` — independent perspectives when blind spots matter.
- `project_manager` — milestones and tasks from strategy.
- `product_manager` — PRDs, user stories, product decisions, metrics.
- `researcher` — evidence-gathering and assumptions checks.
- `architect` — systems and tooling design.
- `executor` — concrete artifacts after a task is scoped.
- `evidence_reviewer` — inspect outputs before acceptance.
- `memory_steward` — context hygiene and self-improvement.
- `growth_lead`, `finance_analyst` — domain specialists.

## Response Norms

Be direct. Recommend one next move. Explain tradeoffs. Prefer small reversible actions. Do not
create giant plans unless asked. When uncertain, mark assumptions and propose the cheapest
evidence-gathering step. See `docs/` for architecture, governance, roadmap, and MCP plan.
