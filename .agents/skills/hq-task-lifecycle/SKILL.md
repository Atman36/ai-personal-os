---
name: hq-task-lifecycle
description: Use when creating, updating, advancing, closing, or validating HQ tasks in 05 AI Control Plane/active-work.json. Trigger on active-work, task lifecycle, queue update, workflow state change, sync task board, validate control plane, or move a task between HQ workflow states.
---

# HQ Task Lifecycle

Use this skill as the single workflow for changing HQ delegated-work state.

## Read First

- `AGENTS.md`
- `python3 scripts/hq_control_plane.py status`
- `05 AI Control Plane/active-work.json`
- `05 AI Control Plane/workflow-registry.json`
- `05 AI Control Plane/operating-policies.json` only when risk, autonomy, approval, or owner authority changes
- relevant `.hq/specs/<task>/LATEST.md` and `.hq/handoffs/<task>/LATEST.md` when the task already exists

## Trigger Shape

Use this skill for requests like:
- "update the queue"
- "move this task"
- "create an active-work task"
- "sync the task board"
- "validate the control plane"

## Default Workflow

1. Identify the task id and current workflow state from `active-work.json` or the startup status.
2. Confirm the task contract is complete: owner, accepting role, workflow, risk tier, autonomy tier, primary update file, next step, acceptance criteria.
3. Make the smallest valid change in `05 AI Control Plane/active-work.json`.
4. If task state changed materially, run `python3 scripts/hq_control_plane.py sync`.
5. Run `python3 scripts/hq_control_plane.py validate`.
6. Report the changed task id, old/new state or next step, validation result, and any remaining founder-only decision.

## Guardrails

- Root `AGENTS.md` and machine-readable control-plane contracts outrank this skill.
- Do not create "almost valid" task records. If required fields are unknown, keep the task in intake or write a blocker instead of inventing policy fields.
- Do not hand-edit `02 Planning/Task Board.md`; render it through `sync`.
- Keep private analysis, raw prospect data, imports, and runtime notes under `.hq/` or outside the repo.
- External sends, public wording, money, legal, destructive actions, hiring, and overrides remain human-owned unless explicit approval exists.

## Expected Output Shape

- Task changed:
- Contract fields checked:
- Files changed:
- Checks run:
- Remaining blocker or next step:
