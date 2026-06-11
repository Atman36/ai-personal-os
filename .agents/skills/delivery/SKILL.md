---
name: delivery
description: Use when you need the HQ Delivery role to turn a scoped task into concrete artifacts, implementation changes, or execution output inside the current authority limits.
---

# Delivery HQ

Use this skill as a thin execution wrapper around the HQ Delivery role.

## Read First

- `AGENTS.md`
- `agents/delivery/AGENTS.md`
- `now.md`
- `projects.md`
- `stack.md`
- `05 AI Control Plane/active-work.json`
- relevant `.hq/specs/<task>/LATEST.md` and `.hq/handoffs/<task>/LATEST.md` when the task already has private continuity
- `05 AI Control Plane/operating-policies.json` when the slice could involve external write, spend, deployment, legal/public commitment, or destructive action

## Trigger Shape

Use this skill for requests like:
- "Delivery"
- "implement this slice"
- "build the artifact"
- "apply the bounded change"
- "finish the task contract"
- "write the handoff"

Do not use this skill for policy decisions, queue management, or shared-truth sync unless Delivery is the explicit owner of the bounded slice.

## Default Workflow

1. Read the active task contract and the narrowest private packet that already exists.
2. Confirm the output expected from the slice and the boundaries you must not cross.
3. Produce the artifact, code change, draft, or execution delta with the smallest useful scope.
4. Keep the execution note short and point it at the primary update file.
5. Leave a handoff note if the slice pauses across sessions.
6. Hand accepted work to Documentation instead of widening the task yourself.

## Guardrails

- Root `AGENTS.md` and the control plane outrank this skill when they conflict.
- Execute only within the task's risk tier and autonomy tier.
- Stop and escalate if the work would create an external write, spend, deployment, legal/public commitment, or destructive action beyond current policy.
- Do not turn bounded execution into strategy or policy ownership.
- Keep private runtime artifacts out of tracked history.

## Expected Output Shape

- Concrete artifact or implementation delta
- Primary update file note
- Real blockers only if the slice cannot continue safely
- Next handoff or acceptance ask
