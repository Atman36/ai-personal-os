# Autonomy and Risk

## Autonomy Tiers

| Tier | Meaning | Examples |
|---|---|---|
| A0 | Advisory only | analysis, questions, options |
| A1 | Draft and prepare | drafts, plans, task specs |
| A2 | Internal execution | local file edits, generated docs, internal scripts |
| A3 | External action with review | email draft ready to send, GitHub issue creation after approval |
| A4 | Human only | money, legal, contracts, public commitments, account/security changes |

## Risk Tiers

| Tier | Meaning |
|---|---|
| low | reversible internal work |
| medium | may affect priorities, reputation, customer/user perception, or significant time |
| high | legal, financial, public, destructive, privacy-sensitive, or irreversible |

## Approval Rules

Governor review is required for high risk and A3/A4. User approval is required before external sends, purchases, deletes, publishing, credentials, and legal/public commitments.

## Harness Escalation

Local Codex/Claude Code is enough for A0-A2 work that is reversible, repo-local, and easy to verify.

Use a harness such as Hermes when work needs any of the following:

- durable checkpoints or replay;
- persistent workspace or environment snapshot;
- parallel agents;
- external connectors or side effects;
- scheduled/background execution;
- high-risk or sensitive-data workflows;
- approval records and artifact bundles;
- recovery after interruption.

When in doubt, keep the work local for analysis/drafting and escalate only the execution step that needs harness guarantees.
