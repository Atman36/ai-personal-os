# Personal OS Routing Matrix

## Front Door Roles

| Request type | First role | Support roles | Typical artifact |
|---|---|---|---|
| “Что делать дальше?” | `chief_of_staff` | `ai_ops_lead`, `ceo` | Top 3 actions + active-work update |
| Strategic choice | `ceo` | `strategy_council`, `researcher`, `finance_analyst` | Decision brief |
| New project | `project_manager` | `product_manager`, `architect`, `growth_lead` | Project intake + task slices |
| Backlog overload | `ai_ops_lead` | `project_manager`, `pm-prioritize` | Ranked backlog |
| Risk/legal/public action | `governor` | `chief_of_staff` | Approval or block note |
| Product feature | `product_manager` | `architect`, `project_manager` | PRD + user stories |
| Research needed | `researcher` | `strategy_council` | Evidence memo |
| Execution / build | `executor` | `architect`, `evidence_reviewer` | Artifact + validation note |
| Weekly review | `ai_ops_lead` | `memory_steward`, `finance_analyst`, `growth_lead` | Weekly operating review |
| Improve OS | `memory_steward` | `ai_ops_lead`, `governor` | Improvement candidate |

## Escalation Criteria

Escalate to `governor` when any item involves:

- money, legal, contracts, privacy, public claims, customer data, credentials;
- destructive file operations or irreversible automation;
- external messages, publishing, outreach, or commitments;
- autonomy expansion from advisory/draft work to execution.

Escalate to `ceo` when:

- priorities conflict;
- a project would displace the current main objective;
- the decision affects positioning, business model, hiring, budget, or strategic narrative.

## WIP Policy

Keep at most 3 active projects and at most 5 active tasks in `this_week` + `executing`. If overloaded, recommend a cut before adding work.
