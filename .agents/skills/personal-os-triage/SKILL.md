---
name: personal-os-triage
description: Use when turning a broad Personal OS request, founder idea, report, blocker, or incoming work item into a scoped Personal OS task contract with owner, accepting role, risk tier, autonomy tier, workflow, primary update file, acceptance criteria, and next step.
---

# Personal OS Context-Aware Triage

> Compatibility note: formerly `hq-context-aware-triage`. The `hq-` name is retired; references now use `personal-os-triage`.

Use this skill before adding or reshaping work in the Personal OS queue.

## Read First

- `AGENTS.md`
- `python3 scripts/osctl.py status`
- `os/05_Control_Plane/agent-registry.json`
- `os/05_Control_Plane/workflow-registry.json`
- `os/05_Control_Plane/operating-policies.json`
- `os/05_Control_Plane/active-work.json` when queue placement, duplication, or ownership matters
- task-local spec/handoff packets only when the incoming work maps to an existing task

## Trigger Shape

Use this skill for requests like:
- "triage this"
- "turn this into a task"
- "who should own this"
- "what risk/autonomy/workflow applies"
- "scope this founder idea"

## Default Workflow

1. Convert the user request into one sentence: desired outcome, artifact, and business reason.
2. Check whether it belongs to an existing active task. Prefer updating a current task over creating a duplicate.
3. Assign owner and accepting role from the role registry.
4. Classify risk tier and autonomy tier from operating policies.
5. Choose the workflow state and required fields from the workflow registry.
6. Set a single primary update file and one concrete next step.
7. Define acceptance criteria that can be checked without reading the whole repo.
8. If queue state changes, use `$personal-os-task-lifecycle` for the actual `active-work.json` edit, sync, and validation.

## Guardrails

- Do not widen context because a request is broad. Start from startup status and the relevant control-plane contracts.
- Ask at most one blocker question when policy, owner, or approval cannot be inferred safely.
- Founder-only authority stays founder-owned: external sends, public/legal claims, budget, destructive changes, hiring, and overrides.
- Keep triage output operational; do not write long strategy documents into tracked files.

## Expected Output Shape

- Proposed task id or existing task:
- Owner / accepting role:
- Risk / autonomy:
- Workflow state:
- Primary update file:
- Acceptance criteria:
- Next step:
- Founder-only approval needed:
