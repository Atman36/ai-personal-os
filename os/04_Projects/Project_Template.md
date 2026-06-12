---
type: overview
project: PROJECTCODE
status: proposed
owner: user
review_cadence: weekly
success_metrics:
  - metric one
risk_tier: low
autonomy_tier: A1
---

# Project: {Name}

- Objective:
- Current next action:
- Risks:
- Decisions:

## Context

## Milestones

## Active Tasks

## Notes

<!--
Minimum project contract (all frontmatter fields above are required):
  type             always "overview" for a project page
  project          short uppercase code used in note names, e.g. {AIMAX}
  status           proposed | active | paused | done | killed
  owner            human or role accountable for the project
  review_cadence   how often the page is reviewed (e.g. weekly)
  success_metrics  list of measurable outcomes
  risk_tier        low | medium | high
  autonomy_tier    A0..A4 default for delegated work in this project

Create a new page with:
  python3 scripts/osctl.py project-new --name "project name" --project CODE
Check all pages with:
  python3 scripts/osctl.py project-index
-->
