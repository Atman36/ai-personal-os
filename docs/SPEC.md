# Personal OS Specification

## Goal

Build a Codex-native personal operating system that can:

- keep current work visible;
- help decide priorities;
- create decision briefs;
- delegate bounded work to specialist agents;
- update tasks and project state;
- run daily and weekly reviews;
- learn from repeated friction;
- add tools safely over time.

## Non-goals for v0

- Fully autonomous external actions.
- Hidden black-box memory.
- Installing hundreds of agents.
- Replacing human judgment for legal, financial, health, or public commitments.

## System Components

### 1. Brain

- Root `AGENTS.md` defines behavior.
- `personal-os-gateway` skill routes requests.
- `personal-os-decision-brief` skill handles decisions.
- Custom Codex agents provide specialized reasoning.

### 2. Memory

- Durable truth: `os/*.md`.
- Machine queue: `os/05_Control_Plane/*.json`.
- Runtime context: `.os_runtime/`.
- Generated mirrors: `Task_Board.md`.

### 3. Hands and legs

- v0: local file edits and Python script.
- v1: GitHub issues/PRs.
- v2: calendar/tasks and Obsidian memory.
- v3: email/Telegram drafts.
- v4: external actions with audit and approval gates.

## Task Contract

Every delegated task must include:

- `id`
- `title`
- `status`
- `project`
- `manager`
- `owner`
- `accepts_result`
- `risk`
- `autonomy`
- `workflow`
- `next`
- `done_when`
- `primary_update_file`

## Decision Contract

Every material decision must include:

- real decision statement;
- options;
- constraints;
- reversibility;
- risks;
- recommendation;
- smallest next step;
- review date;
- evidence that would change the recommendation.

## Proactive Behaviors

Codex should proactively flag:

- stale tasks;
- missing owners;
- WIP overload;
- open decisions blocking tasks;
- risk tier mismatch;
- repeated failures;
- unclear done conditions;
- tasks drifting from North Star.

## Self-Improvement Loop

1. Capture friction in `.os_runtime/reflections/`.
2. Weekly review clusters repeated friction.
3. Candidate improvement is proposed as one of:
   - prompt change;
   - skill change;
   - checklist;
   - script;
   - policy;
   - agent role update.
4. Governor checks whether the change expands autonomy or risk.
5. User approves promotion.
6. Update the file and validate.

## Acceptance Criteria for v0

- `python3 scripts/osctl.py validate` passes.
- `python3 scripts/osctl.py sync` renders Task Board.
- Codex can answer “what should I do next?” from the repo state.
- Codex can create a decision brief.
- Codex can add a task and keep the board synced.
- Weekly review can close/continue/defer tasks.
