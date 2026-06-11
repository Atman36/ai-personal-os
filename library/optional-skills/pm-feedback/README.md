# User Feedback Analysis Skill

![Skill illustration](assets/illustration.png)

Classify user feedback, cluster themes, analyze sentiment and NPS, output Top-10 pains with action recommendations. Part of the Personal Corp product management toolkit.

## Problem

Reviews, support tickets, and survey exports are noisy — pain points hide in volume.

## Solution

The agent classifies feedback into six categories, clusters themes, triangulates sources, and ranks actionable pain points.

## When to use

- After collecting VOC from reviews or support
- Before backlog prioritization
- When NPS dropped and you need themes

## Installation

```bash
cp -r skills/pm-feedback ~/.claude/skills/
```

## Example Prompt

```text
Analyze this feedback spreadsheet and give me the top pain points with recommended actions.
```

Slash command: `/pm-feedback`

## Related skills

- /pm-prioritize
- /pm-prd
- /pm-metrics

## See Also

- [SKILL.md](SKILL.md) — full skill definition
- [README.ru.md](README.ru.md) — Russian version
