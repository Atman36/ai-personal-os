#!/usr/bin/env python3
"""Small local control-plane helper for Personal OS.

No external dependencies. Commands:
  init           Seed personal state files from *.example, then sync.
  validate       Validate active-work task shape and schema contract.
  sync           Render os/02_Planning/Task_Board.md from active-work.json.
  status         Print compact queue status.
  add-task       Add a task to active-work.json.
  decision       Create a decision brief from a title and options.
  reflection-capture
                Capture a private reusable lesson in .os_runtime.
  reflection-review
                Summarize repeated private lessons without promoting them.
  reflection-consume
                Remove active private lessons after a durable improvement ships.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import uuid
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / "os/05_Control_Plane/active-work.json"
ACTIVE_SCHEMA = ROOT / "os/05_Control_Plane/schemas/active-work.schema.json"
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

REQUIRED = ["id", "title", "column", "project", "manager", "owner", "accepts_result", "risk_tier", "autonomy_tier", "workflow", "next_step", "done_when", "primary_update_file"]
COLUMNS = ["inbox", "this_week", "executing", "waiting", "done", "backlog"]
RISKS = {"low", "medium", "high"}
AUTONOMY = {"A0", "A1", "A2", "A3", "A4"}


def now() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9а-яё]+", "-", text, flags=re.I)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:80] or "task"


def load_active_schema() -> Dict[str, Any]:
    if not ACTIVE_SCHEMA.exists():
        return {}
    return json.loads(ACTIVE_SCHEMA.read_text(encoding="utf-8"))


def resolve_schema_ref(schema: Dict[str, Any], ref: str) -> Dict[str, Any]:
    if not ref.startswith("#/"):
        return {}
    current: Any = schema
    for part in ref[2:].split("/"):
        if not isinstance(current, dict):
            return {}
        current = current.get(part)
    return current if isinstance(current, dict) else {}


def json_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    return True


def is_date_string(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_against_schema(value: Any, node: Dict[str, Any], root_schema: Dict[str, Any], path: str = "$") -> List[str]:
    errors: List[str] = []
    if "$ref" in node:
        return validate_against_schema(value, resolve_schema_ref(root_schema, str(node["$ref"])), root_schema, path)

    expected_type = node.get("type")
    if isinstance(expected_type, str) and not json_type(value, expected_type):
        errors.append(f"schema: {path} must be {expected_type}")
        return errors

    if "enum" in node and value not in node["enum"]:
        allowed = ", ".join(repr(item) for item in node["enum"])
        errors.append(f"schema: {path} must be one of {allowed}")

    if isinstance(value, str):
        min_length = node.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            errors.append(f"schema: {path} must not be empty")
        if node.get("format") == "date" and not is_date_string(value):
            errors.append(f"schema: {path} must be YYYY-MM-DD")

    if isinstance(value, dict):
        for field in node.get("required", []):
            if field not in value:
                errors.append(f"schema: {path} missing {field}")
        properties = node.get("properties", {})
        if isinstance(properties, dict):
            for field, child in properties.items():
                if field in value and isinstance(child, dict):
                    errors.extend(validate_against_schema(value[field], child, root_schema, f"{path}.{field}" if path != "$" else field))

    if isinstance(value, list) and isinstance(node.get("items"), dict):
        for index, item in enumerate(value):
            errors.extend(validate_against_schema(item, node["items"], root_schema, f"{path}[{index}]"))

    return errors


def load() -> Dict[str, Any]:
    if not ACTIVE.exists():
        raise SystemExit(f"Missing {ACTIVE}")
    return json.loads(ACTIVE.read_text(encoding="utf-8"))


def save(data: Dict[str, Any]) -> None:
    data["updated_at"] = now()
    ACTIVE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_data(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    schema = load_active_schema()
    if schema:
        errors.extend(validate_against_schema(data, schema, schema))
    ids = set()
    if "tasks" not in data or not isinstance(data["tasks"], list):
        return ["active-work.json must contain a tasks list"]
    for i, task in enumerate(data["tasks"]):
        prefix = f"tasks[{i}]"
        if not isinstance(task, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in REQUIRED:
            if not task.get(field):
                errors.append(f"{prefix} missing {field}")
        tid = task.get("id")
        if tid in ids:
            errors.append(f"duplicate task id: {tid}")
        ids.add(tid)
        if task.get("column") not in COLUMNS:
            errors.append(f"{prefix} invalid column {task.get('column')!r}")
        if task.get("risk_tier") not in RISKS:
            errors.append(f"{prefix} invalid risk_tier {task.get('risk_tier')!r}")
        if task.get("autonomy_tier") not in AUTONOMY:
            errors.append(f"{prefix} invalid autonomy_tier {task.get('autonomy_tier')!r}")
        if task.get("column") == "done" and not task.get("completed_at"):
            errors.append(f"{prefix} missing completed_at")
    active_count = sum(1 for t in data["tasks"] if isinstance(t, dict) and t.get("column") in {"this_week", "executing"})
    if active_count > 5:
        errors.append(f"WIP overload: {active_count} active tasks (limit 5)")
    return errors


def objective_title(data: Dict[str, Any]) -> str:
    objective = data.get("objective", "")
    if isinstance(objective, dict):
        return str(objective.get("title", ""))
    return str(objective)


def render_board(data: Dict[str, Any]) -> str:
    lines = [
        "# Task Board",
        "",
        "> Generated from `os/05_Control_Plane/active-work.json`. Do not edit by hand. Run `python3 scripts/osctl.py sync`.",
        "",
        f"- Updated At: {data.get('updated_at', now())}",
        f"- Operating Mode: {data.get('operating_mode', 'unknown')}",
        f"- Objective: {objective_title(data)}",
        "",
    ]
    tasks = data.get("tasks", [])
    for column in COLUMNS:
        group = [t for t in tasks if t.get("column") == column]
        if not group:
            continue
        title = column.replace("_", " ").title()
        lines += [f"## {title}", ""]
        for t in group:
            lines.append(f"- [{'x' if column == 'done' else ' '}] {t.get('title')}")
            lines.append(f"  - ID: `{t.get('id')}` | Project: {t.get('project')} | Manager: {t.get('manager')} | Owner: {t.get('owner')} | Accepts: {t.get('accepts_result')}")
            lines.append(f"  - Risk: {t.get('risk_tier')} | Autonomy: {t.get('autonomy_tier')} | Workflow: {t.get('workflow')}")
            lines.append(f"  - Next: {t.get('next_step')}")
            lines.append(f"  - Done when: {t.get('done_when')}")
            lines.append(f"  - Primary update file: `{t.get('primary_update_file')}`")
            support = t.get("support") or []
            if support:
                lines.append(f"  - Support: {', '.join(support)}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def normalize_list(values: List[str] | None) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values or []:
        text = normalize_text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def reflections_sessions_dir() -> Path:
    return RUNTIME / "reflections" / "sessions"


def reflection_receipts_dir() -> Path:
    return RUNTIME / "reflections" / "receipts"


def improvements_dir() -> Path:
    return RUNTIME / "improvements"


def reflection_file_for_timestamp(timestamp: str) -> Path:
    return reflections_sessions_dir() / f"{timestamp[:7]}.jsonl"


def build_reflection_payload(args: argparse.Namespace) -> Dict[str, Any]:
    timestamp = utc_timestamp()
    payload = {
        "id": str(uuid.uuid4()),
        "created_at": timestamp,
        "agent": normalize_text(args.agent),
        "task_id": normalize_text(args.task),
        "session_id": normalize_text(args.session),
        "outcome": normalize_text(args.outcome),
        "category": normalize_text(args.category),
        "change_scope": normalize_text(args.change_scope),
        "summary": normalize_text(args.summary),
        "observation": normalize_text(args.observation),
        "issue": normalize_text(args.issue),
        "lesson": normalize_text(args.lesson),
        "proposed_rule": normalize_text(args.proposed_rule),
        "issue_key": slugify(args.issue_key),
        "tags": normalize_list(args.tag),
        "evidence": normalize_list(args.evidence),
    }
    missing = [
        field
        for field in ("agent", "task_id", "session_id", "outcome", "summary", "observation", "issue", "lesson", "issue_key")
        if not payload[field]
    ]
    if missing:
        raise SystemExit("Missing reflection field(s): " + ", ".join(missing))
    return payload


def append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def cmd_reflection_capture(args: argparse.Namespace) -> None:
    payload = build_reflection_payload(args)
    path = reflection_file_for_timestamp(str(payload["created_at"]))
    append_jsonl(path, payload)
    print(f"Captured reflection {payload['id']} in {path.relative_to(ROOT)}")


def iter_reflection_files() -> List[Path]:
    root = reflections_sessions_dir()
    if not root.exists():
        return []
    return sorted(path for path in root.glob("*.jsonl") if path.is_file())


def load_reflections() -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for path in iter_reflection_files():
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON in {path.relative_to(ROOT)}:{line_no}: {exc}") from exc
            if isinstance(payload, dict):
                records.append(payload)
    return records


def build_reflection_review(min_observations: int, min_unique_sessions: int) -> Dict[str, Any]:
    records = load_reflections()
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = slugify(record.get("issue_key") or record.get("issue") or "uncategorized")
        grouped[key].append(record)

    clusters: List[Dict[str, Any]] = []
    for key, items in grouped.items():
        sessions = {normalize_text(item.get("session_id")) for item in items if normalize_text(item.get("session_id"))}
        tasks = {normalize_text(item.get("task_id")) for item in items if normalize_text(item.get("task_id"))}
        ready = len(items) >= min_observations and len(sessions) >= min_unique_sessions
        latest = sorted(items, key=lambda item: str(item.get("created_at", "")))[-1]
        clusters.append(
            {
                "issue_key": key,
                "observations": len(items),
                "unique_sessions": len(sessions),
                "unique_tasks": len(tasks),
                "promotion_call": "ready_to_evaluate" if ready else "keep_private",
                "latest_summary": normalize_text(latest.get("summary")),
                "latest_lesson": normalize_text(latest.get("lesson")),
                "proposed_rule": normalize_text(latest.get("proposed_rule")),
            }
        )
    clusters.sort(key=lambda item: (item["promotion_call"] != "ready_to_evaluate", -item["observations"], item["issue_key"]))
    return {
        "created_at": utc_timestamp(),
        "total_reflections": len(records),
        "ready_count": sum(1 for item in clusters if item["promotion_call"] == "ready_to_evaluate"),
        "min_observations": min_observations,
        "min_unique_sessions": min_unique_sessions,
        "clusters": clusters,
    }


def render_reflection_review(review: Dict[str, Any]) -> str:
    lines = [
        "# Improvement Review",
        "",
        f"- Created At: {review['created_at']}",
        f"- Active Reflections: {review['total_reflections']}",
        f"- Ready To Evaluate: {review['ready_count']}",
        f"- Promotion Threshold: {review['min_observations']} observations across {review['min_unique_sessions']} sessions",
        "",
        "Rule: do not promote a single observation unless the user explicitly asks for the change.",
        "",
    ]
    if not review["clusters"]:
        lines.append("No active private reflections.")
        return "\n".join(lines).rstrip() + "\n"
    for cluster in review["clusters"]:
        lines += [
            f"## {cluster['issue_key']}",
            "",
            f"- Promotion Call: {cluster['promotion_call']}",
            f"- Observations: {cluster['observations']}",
            f"- Unique Sessions: {cluster['unique_sessions']}",
            f"- Unique Tasks: {cluster['unique_tasks']}",
            f"- Latest Summary: {cluster['latest_summary']}",
            f"- Latest Lesson: {cluster['latest_lesson']}",
        ]
        if cluster["proposed_rule"]:
            lines.append(f"- Proposed Rule: {cluster['proposed_rule']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def cmd_reflection_review(args: argparse.Namespace) -> None:
    review = build_reflection_review(args.min_observations, args.min_unique_sessions)
    improvements_dir().mkdir(parents=True, exist_ok=True)
    latest = improvements_dir() / "LATEST.md"
    latest.write_text(render_reflection_review(review), encoding="utf-8")
    print(f"Wrote {latest.relative_to(ROOT)}")
    print(f"Ready to evaluate: {review['ready_count']} / {len(review['clusters'])}")


def cmd_reflection_consume(args: argparse.Namespace) -> None:
    issue_key = slugify(args.issue_key)
    consumed: List[Dict[str, Any]] = []
    for path in iter_reflection_files():
        keep: List[Dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if slugify(record.get("issue_key") or "") == issue_key:
                consumed.append(record)
            else:
                keep.append(record)
        if keep:
            path.write_text("\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in keep) + "\n", encoding="utf-8")
        else:
            path.unlink()
    if not consumed:
        raise SystemExit(f"No active reflections found for issue_key={issue_key}")
    receipt = {
        "id": str(uuid.uuid4()),
        "created_at": utc_timestamp(),
        "issue_key": issue_key,
        "consumed_count": len(consumed),
        "reason": normalize_text(args.reason),
        "source_record_ids": [record.get("id") for record in consumed if record.get("id")],
    }
    path = reflection_receipts_dir() / f"{receipt['created_at'].replace(':', '').replace('-', '')}-{issue_key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Consumed {len(consumed)} reflection(s); receipt: {path.relative_to(ROOT)}")


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
    print(f"Objective: {objective_title(data)}")
    tasks = data.get("tasks", [])
    for column in COLUMNS:
        group = [t for t in tasks if t.get("column") == column]
        if group:
            print(f"\n{column.upper()} ({len(group)})")
            for t in group:
                print(f"- {t['id']}: {t['title']} -> {t['next_step']}")
    active_count = sum(1 for t in tasks if t.get("column") in {"this_week", "executing"})
    print(f"\nActive WIP: {active_count}/5")


def cmd_add(args: argparse.Namespace) -> None:
    data = load()
    tid = args.id or slugify(args.title)
    if any(t.get("id") == tid for t in data.get("tasks", [])):
        raise SystemExit(f"Task id already exists: {tid}")
    task = {
        "id": tid,
        "title": args.title,
        "column": args.column,
        "project": args.project,
        "manager": args.manager,
        "owner": args.owner,
        "accepts_result": args.accepts,
        "risk_tier": args.risk_tier,
        "autonomy_tier": args.autonomy_tier,
        "workflow": args.workflow,
        "next_step": args.next_step,
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
    add.add_argument("--column", "--status", dest="column", choices=COLUMNS, default="inbox")
    add.add_argument("--project", default="Personal OS Bootstrap")
    add.add_argument("--manager", default="chief_of_staff")
    add.add_argument("--owner", default="ai_ops_lead")
    add.add_argument("--accepts", default="user")
    add.add_argument("--risk-tier", "--risk", dest="risk_tier", choices=sorted(RISKS), default="low")
    add.add_argument("--autonomy-tier", "--autonomy", dest="autonomy_tier", choices=sorted(AUTONOMY), default="A1")
    add.add_argument("--workflow", default="task")
    add.add_argument("--next-step", "--next", dest="next_step", required=True)
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
    capture = sub.add_parser("reflection-capture")
    capture.add_argument("--agent", required=True)
    capture.add_argument("--task", required=True)
    capture.add_argument("--session", required=True)
    capture.add_argument("--outcome", default="success")
    capture.add_argument("--category", default="workflow")
    capture.add_argument("--change-scope", default="workflow")
    capture.add_argument("--summary", required=True)
    capture.add_argument("--observation", required=True)
    capture.add_argument("--issue", required=True)
    capture.add_argument("--lesson", required=True)
    capture.add_argument("--proposed-rule", default="")
    capture.add_argument("--issue-key", required=True)
    capture.add_argument("--tag", action="append")
    capture.add_argument("--evidence", action="append")
    capture.set_defaults(func=cmd_reflection_capture)
    review = sub.add_parser("reflection-review")
    review.add_argument("--min-observations", type=int, default=2)
    review.add_argument("--min-unique-sessions", type=int, default=2)
    review.set_defaults(func=cmd_reflection_review)
    consume = sub.add_parser("reflection-consume")
    consume.add_argument("--issue-key", required=True)
    consume.add_argument("--reason", required=True)
    consume.set_defaults(func=cmd_reflection_consume)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
