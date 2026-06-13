---
name: personal-os-spec-handoff
description: Use when creating or refreshing .os_runtime/specs/<task>/LATEST.md or .os_runtime/handoffs/<task>/LATEST.md for Personal OS tasks, especially before multi-session work, delegation, timeout handoff, resuming stale packets, or preserving bounded continuity.
---

# Personal OS Spec Handoff Writer

> Compatibility note: formerly `hq-spec-handoff-writer`. The `hq-` name is retired; references now use `personal-os-spec-handoff`.

Use this skill to write private task packets that preserve continuity without publishing private operating detail.

## Read First

- `AGENTS.md`
- `python3 scripts/osctl.py status`
- `os/05_Control_Plane/active-work.json`
- relevant `.os_runtime/specs/<task>/LATEST.md` and `.os_runtime/handoffs/<task>/LATEST.md` if they already exist
- relevant primary update file only when the task contract points to it and the slice requires it

## Trigger Shape

Use this skill for requests like:
- "write a spec"
- "refresh the handoff"
- "capture continuity"
- "prepare this for another session"
- "record a timeout handoff"

## Default Workflow

1. Identify the task id and whether the slice needs a spec, a handoff, or both.
2. Read only the current task contract and directly relevant packet/update file.
3. Write the packet under `.os_runtime/specs/<task>/LATEST.md` or `.os_runtime/handoffs/<task>/LATEST.md`.
4. Keep the packet private, bounded, and directly resumable.
5. Report the packet path and next action.

## Spec Packet

Write `.os_runtime/specs/<task>/LATEST.md` when the task needs planning, delegation, acceptance criteria, or a stable scope.

Include only:
- task id and updated date
- objective
- in-scope / out-of-scope
- owner, accepting role, risk tier, autonomy tier, workflow
- source files and private inputs used
- acceptance criteria
- verification commands
- open assumptions or founder-only decisions

## Handoff Packet

Write `.os_runtime/handoffs/<task>/LATEST.md` when work will resume later, a long-running tool times out, or another role needs bounded continuity.

Include only:
- current state
- completed work
- changed files or artifacts
- exact next command or next action
- blockers and decisions needed
- verification already run and verification still needed

## Guardrails

- `.os_runtime/` is private runtime state and must remain git-ignored.
- Do not copy raw research, prospect data, credentials, transcripts, telemetry dumps, or private founder notes into tracked files.
- Do not hand-maintain generated summaries; regenerate them through the relevant script.
- Keep packets short enough that the next session can start narrow.

## Expected Output Shape

- Packet written:
- Source context used:
- What changed:
- Next action:
- Verification:
