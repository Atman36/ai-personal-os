# Product Metrics Review Skill

![Skill illustration](assets/illustration.png)

Review product metrics health — trends, anomalies, funnel/retention diagnostics, A/B reads, and OKR alignment. Part of the Personal Corp product management toolkit.

## Problem

Dashboards show movement but not why — teams react to noise instead of root causes.

## Solution

The agent reviews metric trends, decomposes North Star, diagnoses retention/funnel issues, and outputs prioritized actions.

## When to use

- Weekly or monthly metrics review
- After an A/B test concludes
- When OKR pacing looks off

## Installation

```bash
cp -r skills/pm-metrics ~/.claude/skills/
```

## Example Prompt

```text
Review Q1 metrics for feature X: DAU flat, activation down 8%, retention week-4 improved.
```

Slash command: `/pm-metrics`

## Related skills

- /pm-roadmap
- /pm-feedback
- /pm-prioritize

## See Also

- [SKILL.md](SKILL.md) — full skill definition
- [README.ru.md](README.ru.md) — Russian version
