# Analysis of Attached Repositories

## Executive Summary

Best architecture: use **HQ** as the operating kernel, **Obsidian Vault** as personal memory and UX patterns, **Personal Corp Skills** as reusable workflow modules, **The Agency** as a specialist role catalogue, and **Skills for Real Engineers** as engineering discipline for building and improving the OS.

Do not install everything. A personal OS fails when it becomes a museum of prompts. Start with a small core and keep the rest as a library.

## 1. HQ archive

### What it is good for

- Strongest candidate for the kernel.
- Has a clear split between durable truth, machine-readable control plane, human mirrors, private runtime, agents, skills, scripts, schemas, telemetry, permissions, and public-safety gates.
- Useful concepts: `active-work.json`, generated `Task Board.md`, autonomy tiers, risk tiers, Governor, AI Operations Lead, weekly review, spec/handoff packets, self-improvement loop.

### What to change

- Remove project-specific live state before using as your personal OS.
- Simplify scripts for day one; the original HQ scripts are powerful but heavy.
- Keep the governance model and file contract.

## 2. Obsidian Vault archive

### What it is good for

- Strong personal layer: goals, plans, habits, energy, reflection, journals.
- Has the important “front door” idea: OS Gateway hides 100+ assistants behind a small public surface.
- Has a tiering system: core, support, experimental. This is exactly how to avoid prompt overload.

### What to change

- Convert `.mdc` assistants into Codex custom agents only for the top core roles.
- Keep private life/health/journal notes outside the Codex repo unless you explicitly want Codex to reason over them.
- Use the vault as memory source later, not as the first control plane.

## 3. Personal Corp Skills archive

### What it is good for

- Ready-to-use skills for project init, task routing, weekly planning, retros, GitHub issues, CEO council, PRD, prioritization, product work.
- Already has a Codex plugin manifest and a Personal Corp framing: GitHub as an operating system, task routing, weekly cadence.

### What to change

- Install only core skills into `.agents/skills` initially.
- Keep product/media/Telegram skills in `library/optional-skills` until needed.
- Add one Personal OS Gateway skill above them so the user does not need to remember skill names.

## 4. The Agency README

### What it is good for

- Massive specialist catalogue: engineering, product, marketing, sales, finance, security, operations, support, design, and more.
- Use it as a role inspiration library for Codex subagents.

### What to change

- Do not install hundreds of agents into the first OS.
- Extract 10-15 high-leverage roles: CEO, Chief of Staff, AI Ops, Governor, Researcher, Product Manager, Project Manager, Growth, Finance, Architect, Evidence Reviewer, Memory Steward.

## 5. Skills for Real Engineers README

### What it is good for

- Excellent engineering process layer: grilling before implementation, shared language, TDD, diagnose, architecture improvement, issues, handoff.
- Use it when the OS starts producing code or when you build the OS itself.

### What to change

- Keep these as external installable skills. Add them after the Personal OS is already usable.
- Adopt the principles immediately: small composable skills, feedback loops, shared vocabulary, red/green/refactor, architecture review.

## Final Recommendation

Start with this package. It is intentionally smaller than the source archives. It gives Codex a usable kernel and keeps optional material nearby.

Day-one core:

- `AGENTS.md` for global behavior.
- `.codex/agents/*.toml` for specialist subagents.
- `.agents/skills/personal-os-gateway` as front door.
- `os/05_Control_Plane/active-work.json` as queue.
- `scripts/osctl.py` as deterministic sync/status/add-task helper.

Add tools later in this order:

1. GitHub issues and repos.
2. Calendar/tasks.
3. Obsidian memory index.
4. Email/Telegram drafts.
5. External action automation with Governor gates.
