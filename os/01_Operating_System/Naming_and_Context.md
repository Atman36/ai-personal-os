# Naming and Context Hygiene

## Why this matters

Personal OS quality depends on retrieval. If files are named inconsistently, humans cannot scan them and agents cannot reliably find them.

## Durable note filename format

```text
{type} description – YYYY-MM-DD.md
```

For multi-project work:

```text
{PROJECT} {type} description – YYYY-MM-DD.md
```

Examples:

```text
{decision} choose first connector – 2026-06-11.md
{research} harness patterns – 2026-06-11.md
{ACME} {meeting} weekly review – 2026-06-11.md
```

## Rules

- Use a type in curly braces.
- Put the date at the end after an en dash: `–`.
- Keep the description lowercase.
- Keep descriptions short, ideally 3-5 words.
- Use one file for one topic.
- Do not use generic names such as `notes.md`, `meeting.md`, `draft.md`, or `todo.md`.

## Standard types

- `{meeting}` — meeting notes and syncs.
- `{decision}` — decision records and briefs.
- `{research}` — analysis and exploration.
- `{draft}` — work in progress.
- `{rule}` — standards and policies.
- `{prd}` — product requirements.
- `{guide}` — how-to guides.
- `{transcript}` — call/meeting transcripts.
- `{skill}` — skill documentation.
- `{overview}` — high-level summaries.
- `{task}` — task specs.
- `{spec}` — implementation specs.
- `{review}` — weekly/operating reviews.
- `{plan}` — plans and roadmaps.

## CLI helper

Generate a name:

```bash
python3 scripts/osctl.py note-name --type research --description "MCP server comparison" --date 2026-03-18
```

Validate a name:

```bash
python3 scripts/osctl.py note-name --check "{research} mcp server comparison – 2026-03-18.md"
```

## Frontmatter

For durable notes, prefer frontmatter:

```yaml
---
tags:
  - type/decision
  - project/personal-os
date: 2026-06-11
type: decision
status: done
---
```

## Context hygiene for agents

When spawning a subagent or starting a new task, provide a context packet instead of broad chat history:

- objective;
- task id;
- files to read;
- files not to read;
- constraints;
- risk tier and autonomy tier;
- acceptance criteria;
- return format.

Do not paste private raw notes, transcripts, or telemetry into durable project truth. Keep raw material in `.os_runtime/` and promote only accepted summaries.
