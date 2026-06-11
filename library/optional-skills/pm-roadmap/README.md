# Roadmap Update Skill

![Skill illustration](assets/illustration.png)

Sync iteration status into a Now/Next/Later roadmap with delay attribution, health score, and scope-cut framework. Part of the Personal Corp product management toolkit.

## Problem

Roadmaps go stale after one sprint — milestones, delays, and priority shifts are not captured.

## Solution

The agent aggregates sprint status, milestone progress, dependency changes, and outputs an updated roadmap with explicit trade-offs.

## When to use

- End of sprint or iteration
- Before stakeholder review
- When delays need explanation

## Installation

```bash
cp -r skills/pm-roadmap ~/.claude/skills/
```

## Example Prompt

```text
Update the roadmap with Sprint 14 status and Q2 milestones. Two items slipped due to dependency risk.
```

Slash command: `/pm-roadmap`

## Related skills

- /pm-prioritize
- /pm-metrics
- /pm-brainstorm

## See Also

- [SKILL.md](SKILL.md) — full skill definition
- [README.ru.md](README.ru.md) — Russian version
