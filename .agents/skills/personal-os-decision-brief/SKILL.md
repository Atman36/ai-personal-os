---
name: personal-os-decision-brief
description: Create a decision brief for Personal OS. Use when comparing options, choosing a strategy, prioritizing tradeoffs, evaluating risk, deciding what to do next, or when a decision affects money, time allocation, external commitments, product direction, or personal operating model.
---

# Personal OS Decision Brief

## Purpose

Turn an ambiguous choice into a reviewable decision with evidence, tradeoffs, reversibility, and a next action.

## Inputs To Collect

- Decision title
- Context and objective
- Options under consideration
- Constraints: time, money, energy, risk, commitments
- Decision deadline
- What would make the decision wrong
- Required approval owner

If inputs are missing, infer only low-risk placeholders and mark them as assumptions.

## Process

1. Frame the real decision in one sentence.
2. List 2-5 viable options, including “do nothing / defer” when relevant.
3. Score each option on impact, confidence, reversibility, cost, risk, and alignment.
4. Identify one-way-door vs two-way-door aspects.
5. Name hidden dependencies and missing evidence.
6. Recommend one next move: decide now, run a test, collect evidence, or stop.
7. Write the brief to `os/03_Decisions/` when the user asks to persist it.

## Output Template

```markdown
# Decision Brief: {title}

- Date: YYYY-MM-DD
- Owner: user
- Decision type: strategic | operating | project | personal | financial | technical
- Reversibility: one-way | mostly reversible | reversible
- Risk tier: low | medium | high

## 1. Decision
{One sentence}

## 2. Context
{What triggered this and why now}

## 3. Options
| Option | Upside | Cost | Risk | Reversibility | Evidence |
|---|---|---|---|---|---|

## 4. Recommendation
{Recommended option and why}

## 5. Smallest Next Step
{Action that reduces uncertainty or moves execution}

## 6. Approval / Guardrails
{Who must approve and what must not happen}

## 7. Review Date
{When to revisit}
```

## Quality Bar

The recommendation must be falsifiable. Include what evidence would change the recommendation. Avoid generic advice and motivational framing.
