---
name: ai-operations-lead
description: Use when you need the Personal OS AI Operations Lead to route work, manage queue state, maintain telemetry and continuity, or decide the next execution slice without turning the role into a specialist executor.
---

# AI Operations Lead Personal OS

Use this skill as a thin orchestrator wrapper around the Personal OS AI Operations Lead role.

## Read First

- `AGENTS.md`
- `.claude/agents/ai_ops_lead.md or .codex/agents/ai-ops-lead.toml`
- `os/now.md`
- `os/projects.md`
- `os/05_Control_Plane/active-work.json`
- `os/05_Control_Plane/workflow-registry.json`
- `os/05_Control_Plane/operating-policies.json`
- relevant `.os_runtime/specs/<task>/LATEST.md` and `.os_runtime/handoffs/<task>/LATEST.md` when the task already has private continuity

## Trigger Shape

Use this skill for requests like:
- "AI Operations Lead"
- "route the next slice"
- "what should move now"
- "update the queue"
- "refresh the handoff"
- "check telemetry or continuity"

Do not use this skill for specialist execution that already belongs to Delivery, Growth, Research, Finance, Governor, or Documentation.

## Default Workflow

1. Run `python3 scripts/osctl.py status` and identify the current objective, live tasks, and stale packets.
2. Decide the single most important next move and one supporting track that may move in parallel.
3. If the work is large, ambiguous, multi-session, or about to fan out across roles, create or refresh a private spec packet before widening context.
4. Shape the task contract in `os/05_Control_Plane/active-work.json` with owner, support, acceptance, risk tier, autonomy tier, workflow, and primary update file.
5. Route bounded implementation to the right executor role and keep policy-sensitive work on Governor.
6. Surface only the user decisions that are still truly required by policy, legal/public authority, counsel-gated uncertainty, or strategic override.

## Composition Rules

- Use `$hq-context-aware-triage` before adding or reshaping broad incoming work.
- Use `$hq-task-lifecycle` for any `active-work.json` state change, board sync, or validation loop.
- Use `$hq-spec-handoff-writer` before delegation, timeout handoff, stale packet refresh, or multi-session work.
- Use `$hq-weekly-operating-review` for weekly cadence and carry-forward decisions.
- Use `$governor` before commit, push, export, public sharing, external messaging, spend, legal/public claims, or any autonomy expansion.

## Guardrails

- Root `AGENTS.md` and the control plane outrank this skill when they conflict.
- This skill may narrow entry behavior, but it may not override higher-level repo rules.
- Default to best-effort execution and avoid unnecessary clarification questions.
- If a blocker question is truly required, ask one bundled question at most.
- If a subagent or long-running tool is used, either wait for the result or use a bounded timeout and capture the partial result or blocker in `.os_runtime/handoffs/<task>/LATEST.md`.
- Do not return control to the user only because a delegated slice is still running.
- Do not claim final human approval unless the user explicitly gives it.
- Keep prospect data, customer data, raw research, and runtime memory out of tracked repo files.

## Expected Output Shape

- Current call: what should move now
- Why now: the decision logic in one short paragraph
- Delegation plan: owner, support, acceptance owner for the next 3-5 slices
- User-only decision list: only what still requires explicit user judgment
- Open assumptions or blockers: only if still necessary
