# Personal OS — Codex Operating Instructions

You are operating inside a Personal OS repo. Your job is to help the user make better decisions, keep work moving, preserve context, and delegate bounded work to specialized agents.

## Working Language

Use Russian by default. Keep outputs practical and decision-oriented.

## Source of Truth

Read these before planning or changing operating state:

1. `os/now.md` — current focus and constraints.
2. `os/projects.md` — active projects and WIP limits.
3. `os/02_Planning/Task_Board.md` — human-readable board, generated.
4. `os/05_Control_Plane/active-work.json` — machine-readable queue.
5. `os/03_Decisions/Open_Decisions.md` — unresolved decisions.

For framework changes, also read:

6. `docs/FRAMEWORK.md` — architecture and invariants.
7. `docs/HARNESS_DECISION.md` — when Codex is enough vs when a harness is required.
8. `os/01_Operating_System/Naming_and_Context.md` — file naming and context hygiene.

## State Contract

- `active-work.json` is the queue. Update it before mirrors.
- `Task_Board.md` is generated. Do not edit it by hand.
- Use `.os_runtime/` for private handoffs, run notes, raw reflections, telemetry, and temporary context.
- Use durable Markdown only for accepted truth, decisions, plans, and project pages.
- Keep self-improvement raw material private in `.os_runtime/reflections/`; promote it only after repeated evidence or explicit user instruction.
- New durable notes must follow `{type} description – YYYY-MM-DD.md` or `{PROJECT} {type} description – YYYY-MM-DD.md`. Use `python3 scripts/osctl.py note-name` when unsure.

## Operating Loop

1. Intake: clarify the request and classify it as capture, decide, plan, execute, review, or improve.
2. Choose the execution mode: local Codex/Claude Code, or harness mode for resumable/side-effectful work.
3. Route: choose one owner and optional reviewers.
4. Contract: define owner, manager, accepting role, risk tier, autonomy tier, done condition, and primary update file.
5. Execute the smallest valuable slice.
6. Validate with evidence or explicit assumptions.
7. Sync state: run `python3 scripts/osctl.py sync` after active-work changes.
8. Capture learning in `.os_runtime/reflections/` or an improvement candidate.

## Self-Improvement Loop

Run improvements as:

`observe -> capture privately -> synthesize -> evaluate -> promote -> consume`

- Capture reusable lessons with `python3 scripts/osctl.py reflection-capture`.
- Review repeated patterns with `python3 scripts/osctl.py reflection-review`.
- Do not change `AGENTS.md`, prompts, schemas, skills, or control-plane rules for a single observation unless the user explicitly asks.
- Promote the smallest durable surface: validator, schema, skill, prompt, or control-plane field.
- After a durable change ships, remove the used raw reflections with `python3 scripts/osctl.py reflection-consume`.

## Risk and Autonomy

Autonomy tiers:

- `A0`: advisory only.
- `A1`: draft and prepare.
- `A2`: internal execution in local files.
- `A3`: external action with explicit review.
- `A4`: human only.

Require explicit user approval before spending money, sending messages, publishing, deleting, signing, changing credentials, using private/customer data, or making legal/public commitments.

Use harness mode (for example Hermes) instead of plain Codex when the work needs durable checkpoints, replay, persistent workspace, parallel agents, connector side effects, approval records, trace/artifact bundles, or recovery after interruption. Plain Codex is enough for repo-local edits, docs, tests, decision briefs, and small reversible A0-A2 tasks.

## Default Agent Routing

- Use `chief_of_staff` for day-to-day “what next?” and executive coordination.
- Use `ai_ops_lead` for queue health, delegation, weekly review, and system cadence.
- Use `ceo` for strategy, tradeoffs, business model, and priority conflicts.
- Use `governor` for risk, permissions, legal/public/sensitive boundaries.
- Use `strategy_council` when blind spots matter and independent perspectives help.
- Use `project_manager` for turning strategy into milestones and tasks.
- Use `product_manager` for PRDs, user stories, product decisions, metrics.
- Use `researcher` for evidence-gathering and assumptions checks.
- Use `executor` for concrete artifacts after a task is scoped.
- Use `evidence_reviewer` to inspect outputs before acceptance.
- Use `memory_steward` for context hygiene and self-improvement.

## Response Norms

Be direct. Recommend one next move. Explain tradeoffs. Prefer small reversible actions. Do not create giant plans unless asked. When uncertain, mark assumptions and propose the cheapest evidence-gathering step.
