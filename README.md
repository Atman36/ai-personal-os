# Personal OS Starter

A Codex- and Claude-ready starter kit for a personal operating system: decisions, tasks, agents, skills, weekly reviews, and safe delegation.

## What this package is

This is a curated synthesis of the uploaded archives and README repos. It is intentionally smaller than the source material.

- HQ concepts became the control plane.
- Obsidian concepts became the front-door and memory model.
- Personal Corp Skills became the active skill layer.
- The Agency became the role catalogue behind custom agents.
- Skills for Real Engineers became the build discipline.

## Install

```bash
cd personal-os
python3 scripts/osctl.py init       # seed personal state files from *.example
python3 scripts/osctl.py validate
python3 scripts/osctl.py sync
```

Then open this folder in **Codex** (reads `AGENTS.md`) or **Claude Code** (reads `CLAUDE.md`).
Both surfaces share the same skills (`.agents/skills/` ↔ `.claude/skills/`) and the same
control plane.

## First prompt

In Codex:

```text
Открой $personal-os-gateway и проведи daily start.
```

In Claude Code: invoke the `/personal-os-gateway` skill (or say «проведи daily start»).

## Useful prompts

```text
Открой $personal-os-gateway и скажи, что мне делать дальше.
```

```text
Открой $personal-os-decision-brief. Помоги решить, какой проект Personal OS должна вести первым.
```

```text
Spawn chief_of_staff, ai_ops_lead и governor. Пусть они проверят текущую очередь и предложат безопасный next move.
```

```text
Разложи эту инициативу в task contract, добавь в active-work.json и запусти python3 scripts/osctl.py sync.
```

## Key files

- `AGENTS.md` — global instructions for Codex.
- `CLAUDE.md` — global instructions for Claude Code.
- `.codex/agents/` — Codex custom subagents.
- `.claude/agents/` — the same 14 roles as Claude Code subagents.
- `.agents/skills/` — active skills (shared by both surfaces).
- `os/now.md` — current focus.
- `os/projects.md` — active project truth.
- `os/05_Control_Plane/active-work.json` — machine-readable task queue.
- `os/02_Planning/Task_Board.md` — generated human board.
- `scripts/osctl.py` — validate/sync/status/add-task/decision helper.
- `docs/` — architecture, analysis, roadmap, MCP plan, governance.

## Core commands

```bash
python3 scripts/osctl.py init
python3 scripts/osctl.py status
python3 scripts/osctl.py validate
python3 scripts/osctl.py sync
python3 scripts/osctl.py add-task --title "Example" --next "Do the first slice" --done-when "Result is reviewable"
python3 scripts/osctl.py decision --title "Choose first managed project" --option "AI-MAX growth" --option "Personal productivity" --option "Agent corporation"
```

## Privacy

This repo is meant to be public, so it ships the **framework only**. Your personal content is
kept out of git:

- Live state (`os/now.md`, `os/projects.md`, `os/05_Control_Plane/active-work.json`, planning
  and decision files) is gitignored and seeded from committed `*.example` templates.
- Private runtime notes, handoffs, and telemetry live in `.os_runtime/` (gitignored).
- Build/meta notes about creating the OS itself (`SESSION_*.md`, `/_meta/`, `/private/`, etc.)
  are gitignored.

See `.gitignore` for the full list. Run `python3 scripts/osctl.py init` after cloning.

## Operating rule

Do not try to make the OS autonomous on day one. Make it useful first: daily start, decision briefs, task contracts, weekly review, and controlled delegation.
