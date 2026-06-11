---
name: hq-telemetry-event-logger
description: Use when Personal OS operations need structured telemetry events written to .os_runtime/telemetry/ for observability, eval input, or the weekly self-improvement loop. Covers task completions, skill invocations, policy decisions, hook triggers, and session boundaries.
---

# Personal OS Telemetry Event Logger

Use this skill as the single write path for structured telemetry events. Telemetry feeds the weekly operating review, the self-improvement loop, and eval baselines. Write-only at runtime: never edit past events.

## Read First

- `AGENTS.md`
- `.os_runtime/telemetry/` — current month's log directory, named as a year-month child directory
- `os/05_Control_Plane/metrics-registry.json` — which metrics are tracked and how

## Trigger Shape

Use this skill for requests like:
- "log this event"
- "record telemetry"
- "write a telemetry entry"
- "mark this task complete in telemetry"
- "log the hook trigger"

## Event Schema

Each event is a newline-delimited JSON object appended to `.os_runtime/telemetry/YYYY-MM/events.jsonl`:

```json
{
  "ts": "2026-05-03T18:00:00+05:00",
  "event": "task.completed",
  "task_id": "run-first-live-pilot-from-staged-packet",
  "agent": "delivery",
  "session": "optional-session-id",
  "meta": {}
}
```

### Canonical Event Types

| event | when to use |
|---|---|
| `task.created` | new task added to active-work.json |
| `task.advanced` | task moved to next workflow state |
| `task.completed` | task accepted and closed |
| `task.blocked` | task blocked with documented reason |
| `skill.invoked` | named skill used in a session |
| `hook.triggered` | git hook ran (include: hook name, result: ok/blocked) |
| `policy.decision` | policy engine returned allow/block (include: action, decision) |
| `session.start` | session bootstrap completed |
| `session.end` | session closed (include: tasks touched, artifacts changed) |
| `self_improvement.proposal` | improvement filed to .os_runtime/improvements/ |
| `self_improvement.applied` | improvement merged into tracked file |

## Default Workflow

1. Identify the event type from the trigger.
2. Construct the JSON event object with `ts` (ISO 8601 with offset), `event`, and any relevant `task_id`, `agent`, or `meta` fields.
3. Determine the log path: `.os_runtime/telemetry/YYYY-MM/events.jsonl` (create the month directory if absent).
4. Append the event as a single JSON line. Never rewrite existing lines.
5. If the event is a `hook.triggered` with `result: blocked`, also log the violation list in `meta.violations`.
6. Confirm the line was written.

## Guardrails

- `.os_runtime/telemetry/` is private runtime state: never add it to git.
- Do not edit or delete past event lines; append only.
- Do not include prospect names, customer names, or financial values in telemetry `meta` unless the field is explicitly listed in `metrics-registry.json`.
- Do not use this skill to write operating decisions into source-of-truth files; telemetry is observation, not state mutation.

## Expected Output Shape

- Event written: path, event type, ts
- Log file: path
- Line count after write: N
