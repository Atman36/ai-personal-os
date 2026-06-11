#!/usr/bin/env python3
"""Small local control-plane helper for Personal OS.

No external dependencies. Commands:
  init           Seed personal state files from *.example, then sync.
  validate       Validate active-work task shape.
  sync           Render os/02_Planning/Task_Board.md from active-work.json.
  status         Print compact queue status.
  add-task       Add a task to active-work.json.
  decision       Create a decision brief from a title and options.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / "os/05_Control_Plane/active-work.json"
BOARD = ROOT / "os/02_Planning/Task_Board.md"
DECISIONS = ROOT / "os/03_Decisions"
RUNTIME = ROOT / ".os_runtime"

# Personal state files are gitignored. They are seeded from committed *.example
# templates on a fresh clone via `init`. (example, live) pairs:
SEED_PAIRS = [
    ("os/now.example.md", "os/now.md"),
    ("os/projects.example.md", "os/projects.md"),
    ("os/02_Planning/Backlog.example.md", "os/02_Planning/Backlog.md"),
    ("os/02_Planning/Weekly_Plan.example.md", "os/02_Planning/Weekly_Plan.md"),
    ("os/03_Decisions/Decisions.example.md", "os/03_Decisions/Decisions.md"),
    ("os/03_Decisions/Open_Decisions.example.md", "os/03_Decisions/Open_Decisions.md"),
    ("os/05_Control_Plane/active-work.example.json", "os/05_Control_Plane/active-work.json"),
]

REQUIRED = ["id", "title", "status", "project", "manager", "owner", "accepts_result", "risk", "autonomy", "workflow", "next", "done_when", "primary_update_file"]
STATUSES = ["inbox", "this_week", "executing", "waiting", "done", "backlog"]
RISKS = {"low", "medium", "high"}
AUTONOMY = {"A0", "A1", "A2", "A3", "A4"}


def now() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9а-яё]+", "-", text, flags=re.I)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:80] or "task"


def load() -> Dict[str, Any]:
    if not ACTIVE.exists():
        raise SystemExit(f"Missing {ACTIVE}")
    return json.loads(ACTIVE.read_text(encoding="utf-8"))


def save(data: Dict[str, Any]) -> None:
    data["updated_at"] = now()
    ACTIVE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_data(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    ids = set()
    if "tasks" not in data or not isinstance(data["tasks"], list):
        return ["active-work.json must contain a tasks list"]
    for i, task in enumerate(data["tasks"]):
        prefix = f"tasks[{i}]"
        for field in REQUIRED:
            if not task.get(field):
                errors.append(f"{prefix} missing {field}")
        tid = task.get("id")
        if tid in ids:
            errors.append(f"duplicate task id: {tid}")
        ids.add(tid)
        if task.get("status") not in STATUSES:
            errors.append(f"{prefix} invalid status {task.get('status')!r}")
        if task.get("risk") not in RISKS:
            errors.append(f"{prefix} invalid risk {task.get('risk')!r}")
        if task.get("autonomy") not in AUTONOMY:
            errors.append(f"{prefix} invalid autonomy {task.get('autonomy')!r}")
    active_count = sum(1 for t in data["tasks"] if t.get("status") in {"this_week", "executing"})
    if active_count > 5:
        errors.append(f"WIP overload: {active_count} active tasks (limit 5)")
    return errors


def render_board(data: Dict[str, Any]) -> str:
    lines = [
        "# Task Board",
        "",
        "> Generated from `os/05_Control_Plane/active-work.json`. Do not edit by hand. Run `python3 scripts/osctl.py sync`.",
        "",
        f"- Updated At: {data.get('updated_at', now())}",
        f"- Operating Mode: {data.get('operating_mode', 'unknown')}",
        f"- Objective: {data.get('objective', '')}",
        "",
    ]
    tasks = data.get("tasks", [])
    for status in STATUSES:
        group = [t for t in tasks if t.get("status") == status]
        if not group:
            continue
        title = status.replace("_", " ").title()
        lines += [f"## {title}", ""]
        for t in group:
            lines.append(f"- [{'x' if status == 'done' else ' '}] {t.get('title')}")
            lines.append(f"  - ID: `{t.get('id')}` | Project: {t.get('project')} | Manager: {t.get('manager')} | Owner: {t.get('owner')} | Accepts: {t.get('accepts_result')}")
            lines.append(f"  - Risk: {t.get('risk')} | Autonomy: {t.get('autonomy')} | Workflow: {t.get('workflow')}")
            lines.append(f"  - Next: {t.get('next')}")
            lines.append(f"  - Done when: {t.get('done_when')}")
            lines.append(f"  - Primary update file: `{t.get('primary_update_file')}`")
            support = t.get("support") or []
            if support:
                lines.append(f"  - Support: {', '.join(support)}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def cmd_init(_: argparse.Namespace) -> None:
    seeded: List[str] = []
    for example_rel, live_rel in SEED_PAIRS:
        example = ROOT / example_rel
        live = ROOT / live_rel
        if live.exists():
            print(f"skip (exists): {live_rel}")
            continue
        if not example.exists():
            print(f"WARN missing seed: {example_rel}")
            continue
        live.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(example, live)
        seeded.append(live_rel)
        print(f"seeded: {live_rel}")
    cmd_sync(_)
    print(f"Init complete. Seeded {len(seeded)} file(s) from examples.")


def cmd_validate(_: argparse.Namespace) -> None:
    errors = validate_data(load())
    if errors:
        print("INVALID")
        for e in errors:
            print(f"- {e}")
        raise SystemExit(1)
    print("OK: active-work.json is valid")


def cmd_sync(_: argparse.Namespace) -> None:
    data = load()
    errors = validate_data(data)
    if errors:
        print("INVALID; board not rendered")
        for e in errors:
            print(f"- {e}")
        raise SystemExit(1)
    BOARD.write_text(render_board(data), encoding="utf-8")
    RUNTIME.mkdir(exist_ok=True)
    (RUNTIME / "last-sync.json").write_text(json.dumps({"synced_at": datetime.now(timezone.utc).isoformat(), "task_count": len(data.get("tasks", []))}, indent=2), encoding="utf-8")
    print(f"Rendered {BOARD.relative_to(ROOT)}")


def cmd_status(_: argparse.Namespace) -> None:
    data = load()
    print(f"Objective: {data.get('objective','')}")
    tasks = data.get("tasks", [])
    for status in STATUSES:
        group = [t for t in tasks if t.get("status") == status]
        if group:
            print(f"\n{status.upper()} ({len(group)})")
            for t in group:
                print(f"- {t['id']}: {t['title']} -> {t['next']}")
    active_count = sum(1 for t in tasks if t.get("status") in {"this_week", "executing"})
    print(f"\nActive WIP: {active_count}/5")


def cmd_add(args: argparse.Namespace) -> None:
    data = load()
    tid = args.id or slugify(args.title)
    if any(t.get("id") == tid for t in data.get("tasks", [])):
        raise SystemExit(f"Task id already exists: {tid}")
    task = {
        "id": tid,
        "title": args.title,
        "status": args.status,
        "project": args.project,
        "manager": args.manager,
        "owner": args.owner,
        "accepts_result": args.accepts,
        "risk": args.risk,
        "autonomy": args.autonomy,
        "workflow": args.workflow,
        "next": args.next,
        "done_when": args.done_when,
        "primary_update_file": args.primary_update_file,
        "support": args.support or [],
        "tags": args.tags or [],
        "created_at": now(),
        "updated_at": now(),
    }
    data.setdefault("tasks", []).append(task)
    errors = validate_data(data)
    if errors:
        print("INVALID; task not added")
        for e in errors:
            print(f"- {e}")
        raise SystemExit(1)
    save(data)
    print(f"Added task {tid}")


def cmd_decision(args: argparse.Namespace) -> None:
    DECISIONS.mkdir(parents=True, exist_ok=True)
    slug = slugify(args.title)
    path = DECISIONS / f"{now()}-{slug}.md"
    options = args.option or []
    table = "\n".join(f"| {o} |  |  |  |  |  |" for o in options) or "| Option A |  |  |  |  |  |"
    content = f"""# Decision Brief: {args.title}

- Date: {now()}
- Owner: user
- Decision type: {args.type}
- Reversibility: TBD
- Risk tier: {args.risk}

## 1. Decision

{args.question or 'TBD'}

## 2. Context

{args.context or 'TBD'}

## 3. Options

| Option | Upside | Cost | Risk | Reversibility | Evidence |
|---|---|---|---|---|---|
{table}

## 4. Recommendation

TBD

## 5. Smallest Next Step

TBD

## 6. Approval / Guardrails

TBD

## 7. Review Date

TBD
"""
    path.write_text(content, encoding="utf-8")
    print(f"Created {path.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(required=True)
    sub.add_parser("init").set_defaults(func=cmd_init)
    sub.add_parser("validate").set_defaults(func=cmd_validate)
    sub.add_parser("sync").set_defaults(func=cmd_sync)
    sub.add_parser("status").set_defaults(func=cmd_status)
    add = sub.add_parser("add-task")
    add.add_argument("--title", required=True)
    add.add_argument("--id")
    add.add_argument("--status", choices=STATUSES, default="inbox")
    add.add_argument("--project", default="Personal OS Bootstrap")
    add.add_argument("--manager", default="chief_of_staff")
    add.add_argument("--owner", default="ai_ops_lead")
    add.add_argument("--accepts", default="user")
    add.add_argument("--risk", choices=sorted(RISKS), default="low")
    add.add_argument("--autonomy", choices=sorted(AUTONOMY), default="A1")
    add.add_argument("--workflow", default="task")
    add.add_argument("--next", required=True)
    add.add_argument("--done-when", required=True)
    add.add_argument("--primary-update-file", default="os/projects.md")
    add.add_argument("--support", action="append")
    add.add_argument("--tags", action="append")
    add.set_defaults(func=cmd_add)
    dec = sub.add_parser("decision")
    dec.add_argument("--title", required=True)
    dec.add_argument("--question")
    dec.add_argument("--context")
    dec.add_argument("--option", action="append")
    dec.add_argument("--type", default="strategic")
    dec.add_argument("--risk", choices=sorted(RISKS), default="medium")
    dec.set_defaults(func=cmd_decision)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
