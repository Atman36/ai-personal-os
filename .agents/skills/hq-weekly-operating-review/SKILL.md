---
name: hq-weekly-operating-review
description: Use for HQ weekly review, operating review, founder weekly ritual, carry-forward review, queue health review, stale packet review, next-week commitments, or refreshing the weekly operating cadence from the control plane.
---

# HQ Weekly Operating Review

Use this skill for the founder-facing weekly operating ritual. It is a workflow wrapper, not an independent source of truth.

## Read First

- `AGENTS.md`
- `python3 scripts/hq_control_plane.py status`
- `.hq/state/WORKFLOW.generated.md` when available and the review needs a generated summary
- `02 Planning/Weekly Plan.md` only when updating the human working layer
- `05 AI Control Plane/active-work.json`
- task-local spec/handoff packets only for active or stale items being reviewed

## Trigger Shape

Use this skill for requests like:
- "weekly review"
- "operating review"
- "review the week"
- "carry forward tasks"
- "refresh next week commitments"

## Default Workflow

1. State the current objective, active task list, stale packets, and recovery queue from status.
2. Compare this week's commitments against active work; do not infer completion without evidence.
3. Identify tasks to continue, pause, split, close, or escalate.
4. For each material queue change, use `$hq-task-lifecycle` to update `active-work.json`, sync, and validate.
5. If a task needs continuity, use `$hq-spec-handoff-writer` to refresh its private packet.
6. Update `02 Planning/Weekly Plan.md` only when the slice explicitly includes the human weekly working layer.
7. End with founder decisions, next-week commitments, and verification evidence.

## Guardrails

- Do not make strategy, legal, budget, public, or hiring decisions on behalf of the founder.
- Do not turn the weekly review into broad repo exploration.
- Do not hand-edit generated artifacts.
- Keep private task details in `.hq/`; keep tracked summaries public-safe and minimal.

## Expected Output Shape

- Current operating call:
- Continue / pause / close:
- Founder decisions needed:
- Queue changes:
- Files changed:
- Checks run:
- Next week:
