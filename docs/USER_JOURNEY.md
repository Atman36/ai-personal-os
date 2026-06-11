# User Journey

## Day 0 — Install

1. Unzip this folder.
2. Run:

```bash
cd personal-os-codex-starter
python3 scripts/osctl.py validate
python3 scripts/osctl.py sync
```

3. Open the folder in Codex.
4. Prompt:

```text
Открой $personal-os-gateway и проведи daily start.
```

## First 30 minutes

Codex should:

- read the current OS state;
- show current tasks;
- identify the open decision: which project to manage first;
- recommend a next move;
- propose which agents to use.

## First real decision

Prompt:

```text
Открой $personal-os-decision-brief. Решение: какой проект моя Personal OS должна вести первым — AI-MAX growth, личная продуктивность или агентная корпорация.
```

Expected result:

- options scored;
- recommendation;
- smallest test;
- decision brief saved if requested.

## First delegation

Prompt:

```text
Разложи запуск AI-MAX weekly growth loop на task contract и добавь в active-work.json.
```

Expected result:

- task added;
- board synced;
- owner/manager/acceptance/risk/autonomy defined.

## Weekly review

Prompt:

```text
Открой $personal-os-gateway и запусти weekly operating review.
```

Expected result:

- close/continue/defer/kill tasks;
- choose next week outcomes;
- propose OS improvements.
