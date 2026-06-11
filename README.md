# ai-personal-os

A Codex- and Claude Code-ready framework for a personal operating system: priorities, decisions, tasks, governed delegation, context hygiene, weekly review, and safe tool expansion.

## What this framework is

This is not a prompt zoo and not a notes app replacement. It is a small **control plane** that lets an AI assistant operate against explicit state instead of improvising from chat history.

The framework combines:

- local Markdown/JSON as the v0 source of truth;
- `os/05_Control_Plane/active-work.json` as the machine queue;
- generated human mirrors such as `os/02_Planning/Task_Board.md`;
- role-based agents and reusable skills;
- local approval records, risk, autonomy, evidence-review, and self-improvement loops;
- a clear escalation path from local Codex/Claude Code to a durable harness such as Hermes.

The design direction comes from the research in `research/`: Personal OS should evolve from “chat over notes” into a controlled execution system with context assembly, memory, workflow state, approvals, telemetry, and replayable runs.

## Install

```bash
cd ai-personal-os
python3 scripts/osctl.py init
python3 scripts/osctl.py validate-all
python3 scripts/osctl.py sync
```

Then open this folder in **Codex** (reads `AGENTS.md`) or **Claude Code** (reads `CLAUDE.md`). Both surfaces share the same skills through `.agents/skills/` and `.claude/skills`.

## First prompt

In Codex:

```text
Открой $personal-os-gateway и проведи daily start.
```

In Claude Code: invoke the `/personal-os-gateway` skill or say «проведи daily start».

## Useful prompts

```text
Открой $personal-os-gateway и скажи, что мне делать дальше.
```

```text
Открой $personal-os-decision-brief. Помоги решить, какой проект Personal OS должна вести первым.
```

```text
Разложи эту инициативу в task contract, добавь в active-work.json и запусти python3 scripts/osctl.py sync.
```

```text
Прочитай docs/HARNESS_DECISION.md и скажи, эту задачу запускать локально в Codex или в harness.
```

## Key files

- `AGENTS.md` — global instructions for Codex.
- `CLAUDE.md` — global instructions for Claude Code.
- `docs/FRAMEWORK.md` — framework architecture, invariants, and v0/v1 boundary.
- `docs/HARNESS_DECISION.md` — when local Codex/Claude Code is enough vs when Hermes-style harness is required.
- `docs/LOCAL_AGENT_TASKS.md` — implementation task-spec package for local agents.
- `os/01_Operating_System/Naming_and_Context.md` — naming convention and context hygiene rules.
- `.codex/agents/` — Codex custom subagents.
- `.claude/agents/` — the same role catalogue for Claude Code.
- `.agents/skills/` — active skills shared by both surfaces.
- `os/now.md` — current focus.
- `os/projects.md` — active project truth.
- `os/05_Control_Plane/active-work.json` — machine-readable task queue.
- `os/02_Planning/Task_Board.md` — generated human board.
- `scripts/osctl.py` — init/validate/sync/status/add-task/decision/naming helper.
- `research/` — source analyses; prefer `.md` for Mermaid diagrams and `.docx` only when source links are needed.

## Core commands

```bash
python3 scripts/osctl.py init
python3 scripts/osctl.py status
python3 scripts/osctl.py validate
python3 scripts/osctl.py validate-all
python3 scripts/osctl.py sync
python3 scripts/osctl.py note-name --type research --description "MCP server comparison" --date 2026-03-18
python3 scripts/osctl.py add-task --title "Example" --next-step "Do the first slice" --done-when "Result is reviewable"
python3 scripts/osctl.py decision --title "Choose first managed project" --option "AI-MAX growth" --option "Personal productivity" --option "Agent corporation"
python3 scripts/osctl.py approval-request --task-id task-1 --requested-by ai_ops_lead --requested-for github_issue_create --policy-action pause_for_founder_approval --tool-scope github:issues --summary "Create a GitHub issue for task-1" --risk-tier medium --autonomy-tier A3
python3 scripts/osctl.py approval-list
python3 scripts/osctl.py approval-decide --approval approval-id --decision approved --decided-by user
```

## Local Codex vs harness

Use **local Codex/Claude Code** for small, reversible A0-A2 work: docs, repo-local edits, tests, decision briefs, task contracts, and state sync.

Use a **harness such as Hermes** when the work needs any of these: durable checkpoints, replay, persistent workspace, parallel agents, external connectors, side effects, approval records, trace/artifact bundles, long-running execution, or recovery after interruption.

The rule of thumb: if losing the chat would lose the work, or if the task can affect the outside world, run it through a harness.

## Privacy

This repo is meant to be public, so it ships the **framework only**. Your personal content is kept out of git:

- Live state (`os/now.md`, `os/projects.md`, `os/05_Control_Plane/active-work.json`, planning and decision files) is gitignored and seeded from committed `*.example` templates.
- Private runtime notes, handoffs, approvals, artifacts, and telemetry live in `.os_runtime/` (gitignored).
- Build/meta notes about creating the OS itself (`SESSION_*.md`, `/_meta/`, `/private/`, etc.) are gitignored.

See `.gitignore` for the full list. Run `python3 scripts/osctl.py init` after cloning.

## Operating rule

Do not try to make the OS autonomous on day one. Make it useful first: daily start, decision briefs, task contracts, weekly review, context hygiene, and controlled delegation. Add connectors only after the local control plane is coherent and validated.
