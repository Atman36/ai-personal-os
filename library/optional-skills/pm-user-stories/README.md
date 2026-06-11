# User Stories Skill

![Skill illustration](assets/illustration.png)

Break an Epic or large requirement into INVEST-validated User Stories with acceptance criteria and Story Map output. Part of the Personal Corp product management toolkit.

## Problem

A PRD or Epic is too large to ship in one sprint and engineers need independently deliverable units.

## Solution

The agent decomposes the requirement into User Stories with Given-When-Then AC, INVEST checks, Story Points, and a Sprint-ready Story Map.

## When to use

- After PRD review
- Before sprint planning
- When an Epic needs splitting for Jira/Linear/GitHub Issues

## Installation

```bash
cp -r skills/pm-user-stories ~/.claude/skills/
```

## Example Prompt

```text
Break this PRD section into user stories with acceptance criteria and story points.
```

Slash command: `/pm-user-stories`

## Related skills

- /pm-prd
- /pm-prioritize

## See Also

- [SKILL.md](SKILL.md) — full skill definition
- [README.ru.md](README.ru.md) — Russian version
