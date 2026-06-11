# Agent Routing

## Primary Roles

- `chief_of_staff`: day-to-day coordination, next actions, WIP control.
- `ai_ops_lead`: queue, delegation, weekly review, control plane.
- `ceo`: strategy, priorities, hard tradeoffs.
- `governor`: risk, approvals, boundaries.
- `strategy_council`: independent perspectives for important decisions.
- `project_manager`: milestones, tasks, dependencies.
- `product_manager`: product requirements, stories, metrics.
- `researcher`: evidence and assumptions.
- `architect`: system design and integration boundaries.
- `executor`: scoped implementation.
- `evidence_reviewer`: acceptance checks.
- `memory_steward`: context hygiene and self-improvement.

## Fan-out Examples

### Strategic decision

Spawn: `ceo`, `strategy_council`, `finance_analyst`, `growth_lead`, `governor`.

### Build a feature or internal tool

Spawn: `architect`, `product_manager`, `project_manager`, then `executor`, then `evidence_reviewer`.

### Weekly review

Use: `ai_ops_lead`, `chief_of_staff`, `memory_steward`.

## Rule

Never spawn agents just to look busy. Use subagents when independent perspectives reduce risk or parallel exploration saves time.
