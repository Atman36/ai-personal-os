# Decision Scoring

Use a 1-5 scale.

- Impact: size of upside if correct.
- Confidence: quality of evidence.
- Reversibility: 5 means easy to undo, 1 means hard to undo.
- Cost: 5 means cheap in time/money/energy, 1 means expensive.
- Risk: 5 means safe, 1 means dangerous.
- Alignment: fit with `os/now.md`, current projects, values, and strategy.

Default weighted score:

`impact * 2 + confidence + reversibility + cost + risk + alignment * 2`

Do not let the numeric score override a hard constraint. Use the score to clarify tradeoffs, not to fake certainty.
