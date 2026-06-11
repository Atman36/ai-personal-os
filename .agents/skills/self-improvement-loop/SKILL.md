---
name: self-improvement-loop
description: Use when improving Personal OS operating behavior, processing reflections, proposing memory or prompt updates, creating skill candidates, or reviewing whether repeated agent feedback should change AGENTS.md, a role prompt, a skill, a hook, or the control plane.
---

# Self-Improvement Loop

Use this skill to keep Personal OS learning from sessions without turning always-loaded files into logs.

## Read First

- `AGENTS.md`
- `scripts/osctl.py` with `--help` when you need the exact reflection commands
- `.os_runtime/improvements/LATEST.md` when reviewing the latest private synthesis
- relevant `.os_runtime/specs/<task>/LATEST.md` and `.os_runtime/handoffs/<task>/LATEST.md` only when the improvement is tied to a current task

## Trigger Shape

Use this skill for requests like:
- "capture this lesson"
- "run the self-improvement loop"
- "review reflections"
- "should this become a rule"
- "turn repeated feedback into a skill or prompt update"

Do not use it for one-off TODOs, live task status, broad memory dumps, or changes that bypass Governor / CEO approval boundaries.

## Operating Model

Run the loop as:

`observe -> capture privately -> synthesize -> evaluate -> promote -> consume`

Do not write raw session lessons directly into `AGENTS.md`, role prompts, or shared project truth. The active pool is `.os_runtime/reflections/sessions/`; promoted improvement reviews are `.os_runtime/improvements/`; consumed receipts are `.os_runtime/reflections/receipts/`.

## Default Workflow

1. Identify the repeated behavior, failure, or improvement candidate.
2. Capture raw evidence privately under `.os_runtime/reflections/` when it is reusable.
3. Synthesize candidates only after repeated evidence or explicit user instruction.
4. Choose the smallest durable surface: skill, role prompt, validator, schema, hook, or control-plane field.
5. Apply the change only when it respects current approval boundaries.
6. Consume the source reflection records only after the improvement is actually applied.

## Capture A Session Reflection

At session close, write one structured reflection only when there is a reusable lesson:

```bash
python3 scripts/osctl.py reflection-capture \
  --agent "<agent-or-role>" \
  --task "<task-id>" \
  --session "<session-id>" \
  --outcome success \
  --category workflow \
  --change-scope workflow \
  --summary "<short result>" \
  --observation "<concrete observation>" \
  --issue "<underlying repeatable issue>" \
  --lesson "<what should change next time>" \
  --proposed-rule "<optional candidate rule>" \
  --issue-key "<stable-cluster-key>" \
  --tag "<tag>" \
  --evidence "<artifact or command>"
```

Skip capture when the note is just a TODO, temporary status, discoverable code summary, or one-off preference.

## Synthesize Candidates

Daily or weekly, aggregate active reflections:

```bash
python3 scripts/osctl.py reflection-review --min-observations 2 --min-unique-sessions 2
```

This creates private review artifacts only. It must not edit `AGENTS.md`, role prompts, skills, access rules, safety rules, shared truth, or production logic.

## Promotion Rules

Promote only after repeated evidence or explicit user instruction.

- Procedure or repeated checklist: create or update a skill.
- Role behavior: update the narrow role prompt or role skill.
- Workflow state or acceptance field: update the control plane and validate it.
- Critical enforceable rule: prefer hook, test, validator, or schema.
- Universal short rule: consider `AGENTS.md` only if it applies to almost every session.
- Temporary context: discard.

Before promotion, check for duplicates, conflicts, and whether the candidate can be enforced outside prose.

## Consume Used Records

After an improvement has actually been applied, remove the source records from the active reflection pool:

```bash
python3 scripts/osctl.py reflection-consume \
  --issue-key "<stable-cluster-key>" \
  --reason "<what was changed>"
```

This deletes matching active records and writes only a small receipt without raw content. If the improvement was not applied, do not consume the records.

## Legacy Migration

If flat files exist directly under `.os_runtime/reflections/`, do not promote them automatically. Convert only reusable records into structured `reflection-capture` entries, then archive or delete the loose files.

## Guardrails

- Keep `.os_runtime/` private and untracked.
- Do not retain raw reflections after they have been used to improve the project.
- Do not use reflection review as approval to change safety, access, production, public, legal, or spend behavior.
- If a candidate touches restricted surfaces, keep it manual-only and escalate to Governor or CEO.

## Expected Output Shape

- Improvement call: apply now, keep private, escalate, or discard
- Evidence: the repeated observation or explicit instruction behind the call
- Changed surface: the exact skill, prompt, validator, schema, hook, or control-plane field affected
- Verification: the command or review that proved the change
- Remaining boundary: any approval or policy limit that still applies
