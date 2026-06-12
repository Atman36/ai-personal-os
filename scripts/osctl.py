#!/usr/bin/env python3
"""Small local control-plane helper for Personal OS.

No external dependencies. Commands:
  init           Seed personal state files from *.example, then sync.
  validate       Validate active-work task shape and schema contract.
  validate-all   Validate active work plus committed control-plane registries.
  sync           Render os/02_Planning/Task_Board.md from active-work.json.
  status         Print compact queue status.
  add-task       Add a task to active-work.json.
  decision       Create a decision brief from a title and options.
  note-name      Format or validate Personal OS note filenames.
  reflection-capture
                Capture a private reusable lesson in .os_runtime.
  reflection-review
                Summarize repeated private lessons without promoting them.
  reflection-consume
                Remove active private lessons after a durable improvement ships.
  run-start      Start a run record under .os_runtime/runs/YYYY-MM/.
  run-step       Append a step to an active run record.
  run-finish     Finish a run with status, verification, and artifacts.
  run-receipt    Render a Markdown receipt next to the run record.
  approval-request
                Create a local approval record under .os_runtime.
  approval-decide
                Approve, reject, or block a pending approval record.
  approval-list  List local approval records.
  context-pack   Build a context packet for spawning a subagent on a task.
  project-new    Create a typed project page in os/04_Projects/.
  project-index  Scan project pages and report missing contract fields.
  telemetry-log  Append a validated telemetry event to .os_runtime/telemetry/.
  telemetry-report
                Render a weekly telemetry report by workflow/status/actor/event.
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
CONTROL_PLANE = ROOT / "os/05_Control_Plane"
SCHEMAS = CONTROL_PLANE / "schemas"
APPROVAL_SCHEMA = SCHEMAS / "approval.schema.json"

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
STANDARD_NOTE_TYPES = {
    "meeting", "decision", "research", "draft", "rule", "prd", "guide",
    "transcript", "skill", "overview", "task", "spec", "review", "plan",
}
# Local run records (Task 01): a small subset of schemas/run.schema.json that
# stays sufficient for resume/inspect without the full harness contract.
RUN_REQUIRED = ["run_id", "task_id", "workflow", "actor", "status", "started_at", "updated_at", "artifact_paths", "verification", "approval_ids"]
RUN_FINAL_STATUSES = {"completed", "failed", "cancelled"}
RUN_STATUSES = RUN_FINAL_STATUSES | {"running", "waiting_approval", "blocked"}
STEP_STATUSES = {"completed", "failed", "blocked", "skipped"}
POLICY_ACTIONS = {"allow", "allow_with_review", "pause_for_founder_approval", "block"}
APPROVAL_DECISIONS = {"approved", "rejected", "blocked"}
APPROVAL_REQUIRED = [
    "schema_version",
    "entity_type",
    "id",
    "task_id",
    "thread_id",
    "mission_id",
    "run_id",
    "step_id",
    "requested_by",
    "requested_for",
    "policy_action",
    "approval_key",
    "status",
    "decision",
    "tool_scope",
    "policy_context",
    "risk_tier",
    "autonomy_tier",
    "summary",
    "rationale",
    "requested_at",
    "updated_at",
    "decided_at",
    "decided_by",
    "metadata",
]
NOTE_NAME_RE = re.compile(
    r"^(?:\{(?P<project>[A-Z0-9][A-Z0-9_-]*)\} )?"
    r"\{(?P<type>[a-z][a-z0-9_-]*)\} "
    r"(?P<description>.+) – (?P<date>\d{4}-\d{2}-\d{2})\.md$"
)


def now() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9а-яё]+", "-", text, flags=re.I)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:80] or "task"


def clean_note_description(text: str) -> str:
    """Return a short, filename-safe, lower-case note description."""
    text = text.lower().strip()
    text = re.sub(r"[^0-9a-zа-яё ]+", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()
    return text or "untitled"


def format_note_name(note_type: str, description: str, note_date: str | None = None, project: str | None = None) -> str:
    note_type = note_type.strip().strip("{}").lower()
    if not note_type:
        raise SystemExit("Missing note type")
    note_date = note_date or now()
    if not is_date_string(note_date):
        raise SystemExit("Date must be YYYY-MM-DD")
    clean_description = clean_note_description(description)
    prefix = ""
    if project:
        project_code = re.sub(r"[^A-Z0-9_-]+", "", project.strip().upper())
        if not project_code:
            raise SystemExit("Project code must contain A-Z, 0-9, _ or -")
        prefix = f"{{{project_code}}} "
    return f"{prefix}{{{note_type}}} {clean_description} – {note_date}.md"


def validate_note_name(filename: str) -> List[str]:
    name = Path(filename).name
    errors: List[str] = []
    match = NOTE_NAME_RE.match(name)
    if not match:
        return ["filename must match `{type} description – YYYY-MM-DD.md` or `{PROJECT} {type} description – YYYY-MM-DD.md`"]
    note_type = match.group("type")
    description = match.group("description")
    note_date = match.group("date")
    if note_type not in STANDARD_NOTE_TYPES:
        errors.append(f"unknown type {{{note_type}}}; add it deliberately if this is a new standard type")
    if description != description.lower():
        errors.append("description must be lowercase")
    if re.search(r"[^0-9a-zа-яё ]", description, flags=re.I):
        errors.append("description must not contain punctuation or special characters")
    if len(description.split()) > 7:
        errors.append("description should stay short; target 3-5 words")
    if not is_date_string(note_date):
        errors.append("date must be YYYY-MM-DD")
    return errors


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
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def is_date_string(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def is_datetime_string(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate_against_schema(value: Any, node: Dict[str, Any], root_schema: Dict[str, Any], path: str = "$") -> List[str]:
    errors: List[str] = []
    if "$ref" in node:
        return validate_against_schema(value, resolve_schema_ref(root_schema, str(node["$ref"])), root_schema, path)

    for child in node.get("allOf", []) if isinstance(node.get("allOf"), list) else []:
        if isinstance(child, dict):
            errors.extend(validate_against_schema(value, child, root_schema, path))

    if "const" in node and value != node["const"]:
        errors.append(f"schema: {path} must be {node['const']!r}")

    expected_type = node.get("type")
    if isinstance(expected_type, list):
        if not any((item == "null" and value is None) or (isinstance(item, str) and json_type(value, item)) for item in expected_type):
            errors.append(f"schema: {path} must be one of {', '.join(map(str, expected_type))}")
            return errors
    elif isinstance(expected_type, str) and not json_type(value, expected_type):
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
        if node.get("format") == "date-time" and not is_datetime_string(value):
            errors.append(f"schema: {path} must be an ISO date-time")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = node.get("minimum")
        if isinstance(minimum, (int, float)) and value < minimum:
            errors.append(f"schema: {path} must be >= {minimum}")

    if isinstance(value, dict):
        min_properties = node.get("minProperties")
        if isinstance(min_properties, int) and len(value) < min_properties:
            errors.append(f"schema: {path} must contain at least {min_properties} properties")
        for field in node.get("required", []):
            if field not in value:
                errors.append(f"schema: {path} missing {field}")
        properties = node.get("properties", {})
        if isinstance(properties, dict):
            for field, child in properties.items():
                if field in value and isinstance(child, dict):
                    errors.extend(validate_against_schema(value[field], child, root_schema, f"{path}.{field}" if path != "$" else field))
        additional = node.get("additionalProperties")
        if isinstance(additional, dict) and isinstance(properties, dict):
            for field, child_value in value.items():
                if field not in properties:
                    errors.extend(validate_against_schema(child_value, additional, root_schema, f"{path}.{field}" if path != "$" else field))
        elif additional is False and isinstance(properties, dict):
            for field in value:
                if field not in properties:
                    errors.append(f"schema: {path} unexpected {field}")

    if isinstance(value, list) and isinstance(node.get("items"), dict):
        min_items = node.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            errors.append(f"schema: {path} must contain at least {min_items} item(s)")
        for index, item in enumerate(value):
            errors.extend(validate_against_schema(item, node["items"], root_schema, f"{path}[{index}]"))

    return errors


def validate_json_file(path: Path, schema_path: Path) -> List[str]:
    if not path.exists():
        return [f"missing file: {path.relative_to(ROOT)}"]
    if not schema_path.exists():
        return [f"missing schema: {schema_path.relative_to(ROOT)}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path.relative_to(ROOT)} invalid JSON: {exc}"]
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{schema_path.relative_to(ROOT)} invalid JSON: {exc}"]
    return [f"{path.relative_to(ROOT)}: {error}" for error in validate_against_schema(value, schema, schema)]


def control_plane_schema_targets() -> List[tuple[Path, Path]]:
    return [
        (ACTIVE, ACTIVE_SCHEMA),
        (CONTROL_PLANE / "agent-registry.json", SCHEMAS / "agent-registry.schema.json"),
        (CONTROL_PLANE / "metrics-registry.json", SCHEMAS / "metrics-registry.schema.json"),
        (CONTROL_PLANE / "operating-policies.json", SCHEMAS / "operating-policies.schema.json"),
        (CONTROL_PLANE / "workflow-registry.json", SCHEMAS / "workflow-registry.schema.json"),
    ]


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


def runs_dir() -> Path:
    return RUNTIME / "runs"


def run_artifacts_dir(run_id: str) -> Path:
    return RUNTIME / "artifacts" / run_id


def approvals_dir() -> Path:
    return RUNTIME / "approvals"


def validate_run_record(record: Dict[str, Any]) -> List[str]:
    errors = [f"missing {field}" for field in RUN_REQUIRED if field not in record]
    if "status" in record and record["status"] not in RUN_STATUSES:
        errors.append(f"invalid status {record['status']!r}")
    return errors


def validate_approval_record(record: Dict[str, Any]) -> List[str]:
    errors = [f"missing {field}" for field in APPROVAL_REQUIRED if field not in record]
    if "policy_action" in record and record["policy_action"] not in POLICY_ACTIONS:
        errors.append(f"invalid policy_action {record['policy_action']!r}")
    if "risk_tier" in record and record["risk_tier"] not in RISKS:
        errors.append(f"invalid risk_tier {record['risk_tier']!r}")
    if "autonomy_tier" in record and record["autonomy_tier"] not in AUTONOMY:
        errors.append(f"invalid autonomy_tier {record['autonomy_tier']!r}")
    if record.get("status") not in {"pending", "decided"}:
        errors.append(f"invalid status {record.get('status')!r}")
    decision = record.get("decision")
    if record.get("status") == "pending" and decision:
        errors.append("pending approval must not have a decision")
    if record.get("status") == "decided" and decision not in APPROVAL_DECISIONS:
        errors.append("decided approval must have approved, rejected, or blocked decision")
    if APPROVAL_SCHEMA.exists():
        schema = json.loads(APPROVAL_SCHEMA.read_text(encoding="utf-8"))
        errors.extend(validate_against_schema(record, schema, schema))
    return errors


def find_run_record(run_id: str) -> Path:
    if runs_dir().exists():
        for path in sorted(runs_dir().glob(f"*/{run_id}.json")):
            return path
    raise SystemExit(f"Run not found: {run_id}")


def load_run(run_id: str) -> tuple[Path, Dict[str, Any]]:
    path = find_run_record(run_id)
    return path, json.loads(path.read_text(encoding="utf-8"))


def save_run(path: Path, record: Dict[str, Any]) -> None:
    record["updated_at"] = utc_timestamp()
    errors = validate_run_record(record)
    if errors:
        raise SystemExit("Invalid run record: " + "; ".join(errors))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def find_approval_record(approval_id: str) -> Path:
    if approvals_dir().exists():
        for path in sorted(approvals_dir().glob(f"*/{approval_id}.json")):
            return path
    raise SystemExit(f"Approval not found: {approval_id}")


def load_approval(approval_id: str) -> tuple[Path, Dict[str, Any]]:
    path = find_approval_record(approval_id)
    return path, json.loads(path.read_text(encoding="utf-8"))


def save_approval(path: Path, record: Dict[str, Any]) -> None:
    record["updated_at"] = utc_timestamp()
    errors = validate_approval_record(record)
    if errors:
        raise SystemExit("Invalid approval record: " + "; ".join(errors))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def list_approvals(status: str = "all") -> List[tuple[Path, Dict[str, Any]]]:
    records: List[tuple[Path, Dict[str, Any]]] = []
    if not approvals_dir().exists():
        return records
    for path in sorted(approvals_dir().glob("*/*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if status != "all" and record.get("status") != status:
            continue
        records.append((path, record))
    records.sort(key=lambda item: (str(item[1].get("requested_at", "")), str(item[1].get("id", ""))))
    return records


def cmd_run_start(args: argparse.Namespace) -> None:
    run_id = normalize_text(args.run_id) or f"run-{now()}-{uuid.uuid4().hex[:8]}"
    if runs_dir().exists() and any(runs_dir().glob(f"*/{run_id}.json")):
        raise SystemExit(f"Run id already exists: {run_id}")
    started = utc_timestamp()
    record = {
        "run_id": run_id,
        "task_id": args.task,
        "workflow": args.workflow,
        "actor": args.actor,
        "status": "running",
        "started_at": started,
        "updated_at": started,
        "finished_at": "",
        "steps": [],
        "artifact_paths": [],
        "verification": {"summary": "", "evidence": []},
        "approval_ids": [],
    }
    path = runs_dir() / started[:7] / f"{run_id}.json"
    save_run(path, record)
    run_artifacts_dir(run_id).mkdir(parents=True, exist_ok=True)
    print(f"Started run {run_id}")
    print(f"Record: {path.relative_to(ROOT)}")
    print(f"Artifacts: {run_artifacts_dir(run_id).relative_to(ROOT)}")


def cmd_run_step(args: argparse.Namespace) -> None:
    path, record = load_run(args.run)
    if record.get("status") in RUN_FINAL_STATUSES:
        raise SystemExit(f"Run {args.run} is already {record['status']}; cannot append steps")
    step = {
        "index": len(record.get("steps", [])) + 1,
        "summary": args.summary,
        "status": args.status,
        "evidence": normalize_list(args.evidence),
        "created_at": utc_timestamp(),
    }
    record.setdefault("steps", []).append(step)
    save_run(path, record)
    print(f"Appended step {step['index']} to {path.relative_to(ROOT)}")


def cmd_run_finish(args: argparse.Namespace) -> None:
    path, record = load_run(args.run)
    record["status"] = args.status
    record["finished_at"] = utc_timestamp()
    record["verification"] = {"summary": normalize_text(args.verification), "evidence": normalize_list(args.evidence)}
    record["artifact_paths"] = normalize_list(list(record.get("artifact_paths") or []) + list(args.artifact or []))
    record["approval_ids"] = normalize_list(list(record.get("approval_ids") or []) + list(args.approval_id or []))
    save_run(path, record)
    print(f"Finished run {args.run} as {args.status}")
    print(f"Record: {path.relative_to(ROOT)}")


def render_run_receipt(record: Dict[str, Any]) -> str:
    verification = record.get("verification") or {}
    lines = [
        f"# Run Receipt: {record['run_id']}",
        "",
        f"- Task: {record['task_id']}",
        f"- Workflow: {record['workflow']}",
        f"- Actor: {record['actor']}",
        f"- Status: {record['status']}",
        f"- Started At: {record['started_at']}",
        f"- Finished At: {record.get('finished_at') or 'in progress'}",
        f"- Verification: {verification.get('summary') or 'none recorded'}",
        "",
        "## Steps",
        "",
    ]
    steps = record.get("steps") or []
    for step in steps:
        lines.append(f"{step.get('index')}. [{step.get('status')}] {step.get('summary')}")
        for item in step.get("evidence") or []:
            lines.append(f"   - evidence: {item}")
    if not steps:
        lines.append("None.")
    lines += ["", "## Artifacts", ""]
    lines += [f"- `{p}`" for p in record.get("artifact_paths") or []] or ["None."]
    lines += ["", "## Approvals", ""]
    lines += [f"- {a}" for a in record.get("approval_ids") or []] or ["None."]
    return "\n".join(lines).rstrip() + "\n"


def cmd_run_receipt(args: argparse.Namespace) -> None:
    path, record = load_run(args.run)
    receipt = path.with_name(f"{record['run_id']}-receipt.md")
    receipt.write_text(render_run_receipt(record), encoding="utf-8")
    print(f"Receipt: {receipt.relative_to(ROOT)}")


def cmd_approval_request(args: argparse.Namespace) -> None:
    approval_id = normalize_text(args.id) or f"approval-{now()}-{uuid.uuid4().hex[:8]}"
    if approvals_dir().exists() and any(approvals_dir().glob(f"*/{approval_id}.json")):
        raise SystemExit(f"Approval id already exists: {approval_id}")
    tool_scope = normalize_list(args.tool_scope)
    payload = {
        "schema_version": 1,
        "entity_type": "approval",
        "id": approval_id,
        "task_id": normalize_text(args.task_id),
        "thread_id": normalize_text(args.thread_id),
        "mission_id": normalize_text(args.mission_id),
        "run_id": normalize_text(args.run_id),
        "step_id": normalize_text(args.step_id),
        "requested_by": normalize_text(args.requested_by),
        "requested_for": normalize_text(args.requested_for),
        "policy_action": normalize_text(args.policy_action),
        "approval_key": {
            "task_id": normalize_text(args.task_id),
            "requested_for": normalize_text(args.requested_for),
            "policy_action": normalize_text(args.policy_action),
            "tool_scope": tool_scope,
        },
        "status": "pending",
        "decision": "",
        "tool_scope": tool_scope,
        "policy_context": {
            "risk_tier": normalize_text(args.risk_tier),
            "autonomy_tier": normalize_text(args.autonomy_tier),
        },
        "risk_tier": normalize_text(args.risk_tier),
        "autonomy_tier": normalize_text(args.autonomy_tier),
        "summary": normalize_text(args.summary),
        "rationale": normalize_text(args.rationale),
        "requested_at": utc_timestamp(),
        "updated_at": utc_timestamp(),
        "decided_at": "",
        "decided_by": "",
        "metadata": {},
    }
    missing = [
        field
        for field in (
            "task_id",
            "requested_by",
            "requested_for",
            "policy_action",
            "summary",
            "risk_tier",
            "autonomy_tier",
        )
        if not payload[field]
    ]
    if not tool_scope:
        missing.append("tool_scope")
    if missing:
        raise SystemExit("Missing approval field(s): " + ", ".join(missing))
    path = approvals_dir() / str(payload["requested_at"])[:7] / f"{approval_id}.json"
    save_approval(path, payload)
    print(f"Requested approval {approval_id}")
    print(f"Record: {path.relative_to(ROOT)}")


def cmd_approval_decide(args: argparse.Namespace) -> None:
    if args.decision == "approved" and not normalize_text(args.decided_by):
        raise SystemExit("approved decisions require --decided-by")
    path, record = load_approval(args.approval)
    if record.get("status") == "decided":
        raise SystemExit(f"Approval {args.approval} is already decided")
    record["status"] = "decided"
    record["decision"] = normalize_text(args.decision)
    record["decided_by"] = normalize_text(args.decided_by)
    record["decided_at"] = utc_timestamp()
    record["rationale"] = normalize_text(args.rationale) or normalize_text(record.get("rationale"))
    save_approval(path, record)
    print(f"Decided approval {args.approval}: {args.decision}")
    print(f"Record: {path.relative_to(ROOT)}")


def cmd_approval_list(args: argparse.Namespace) -> None:
    records = list_approvals(status=args.status)
    if not records:
        print("No approval records.")
        return
    for path, record in records:
        decision = record.get("decision") or "pending"
        print(
            f"- {record.get('id')}: {record.get('status')} / {decision} | "
            f"{record.get('task_id')} | {record.get('summary')} | {path.relative_to(ROOT)}"
        )


def agent_registry_path() -> Path:
    return CONTROL_PLANE / "agent-registry.json"


def workflow_registry_path() -> Path:
    return CONTROL_PLANE / "workflow-registry.json"


def projects_dir() -> Path:
    return ROOT / "os/04_Projects"


def context_packs_dir() -> Path:
    return RUNTIME / "context-packs"


def telemetry_dir() -> Path:
    return RUNTIME / "telemetry"


def load_json(path: Path, label: str) -> Dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing {label}: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {label} {path}: {exc}") from exc


def find_task(data: Dict[str, Any], task_id: str) -> Dict[str, Any]:
    tasks = [t for t in data.get("tasks", []) if isinstance(t, dict)]
    for task in tasks:
        if task.get("id") == task_id:
            return task
    known = ", ".join(str(t.get("id")) for t in tasks) or "none"
    raise SystemExit(f"Task not found: {task_id} (known ids: {known})")


def find_role(registry: Dict[str, Any], role_id: str) -> Dict[str, Any]:
    roles = [r for r in registry.get("roles", []) if isinstance(r, dict)]
    for role in roles:
        if role.get("id") == role_id:
            return role
    known = ", ".join(str(r.get("id")) for r in roles) or "none"
    raise SystemExit(f"Unknown role: {role_id} (known roles: {known})")


def build_context_pack(task: Dict[str, Any], role: Dict[str, Any], registry: Dict[str, Any], objective: str) -> str:
    """Render a Markdown context packet per os/01_Operating_System/Naming_and_Context.md."""
    constraints = list((registry.get("principal_contract") or {}).get("default_constraints") or [])
    memory_boundary = ""
    for grant in registry.get("capability_grants") or []:
        if isinstance(grant, dict) and grant.get("role_id") == role.get("id"):
            memory_boundary = normalize_text(grant.get("memory_boundary"))
    read_files = [
        "os/now.md",
        "os/projects.md",
        "os/05_Control_Plane/active-work.json",
        str(task.get("primary_update_file")),
    ]
    for routing in registry.get("capability_routing") or []:
        if isinstance(routing, dict) and routing.get("id") == task.get("workflow"):
            read_files.extend(str(p) for p in routing.get("evidence") or [])
    read_files = normalize_list(read_files)
    lines = [
        f"# Context Packet: {task['id']} -> {role['id']}",
        "",
        f"- Generated At: {utc_timestamp()}",
        f"- Objective: {objective}",
        f"- Role: {role.get('display_name')} ({role.get('id')}) — {role.get('mission')}",
        f"- Manager: {task.get('manager')} | Owner: {task.get('owner')} | Accepts result: {task.get('accepts_result')}",
        f"- Risk tier: {task.get('risk_tier')} | Autonomy tier: {task.get('autonomy_tier')} (role default: {role.get('default_autonomy_tier')})",
        "",
        "## Task Contract",
        "",
        f"- ID: `{task.get('id')}`",
        f"- Title: {task.get('title')}",
        f"- Column: {task.get('column')}",
        f"- Project: {task.get('project')}",
        f"- Workflow: {task.get('workflow')}",
        f"- Next step: {task.get('next_step')}",
        f"- Done when: {task.get('done_when')}",
        f"- Primary update file: `{task.get('primary_update_file')}`",
    ]
    support = task.get("support") or []
    if support:
        lines.append(f"- Support roles: {', '.join(support)}")
    lines += [
        "",
        "## Files To Read (pointers only)",
        "",
    ]
    lines += [f"- `{path}`" for path in read_files]
    lines += [
        "",
        "## Files Not To Read",
        "",
        "- Private vault folders (diary/journal/health/therapy/private/messages).",
        "- Raw `.os_runtime/` reflections, telemetry, or session logs outside this task.",
        "- Global chat history; this packet is the full intended context.",
        "",
        "## Constraints",
        "",
    ]
    lines += [f"- {constraint}" for constraint in constraints]
    if memory_boundary:
        lines.append(f"- Memory boundary: {memory_boundary}")
    lines += [
        "- Do not paste raw private data into durable files; reference pointers instead.",
        "",
        "## Acceptance Criteria",
        "",
        f"- Done when: {task.get('done_when')}",
        f"- Result is accepted by: {task.get('accepts_result')}",
        "",
        "## Return Format",
        "",
        "1. Summary of what was done (3-5 sentences).",
        "2. Changed files or artifact paths.",
        "3. Verification evidence (commands run, checks performed).",
        "4. Open questions or assumptions.",
        "5. Recommended next step for the manager.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def cmd_context_pack(args: argparse.Namespace) -> None:
    data = load()
    task = find_task(data, args.task)
    registry = load_json(agent_registry_path(), "agent registry")
    role = find_role(registry, args.role)
    packet = build_context_pack(task, role, registry, objective_title(data))
    path = context_packs_dir() / str(task["id"]) / f"{role['id']}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(packet, encoding="utf-8")
    print(f"Context packet: {path.relative_to(ROOT)}")


# Project entity model v0 (Task 04): minimum contract for a project page.
PROJECT_REQUIRED_FIELDS = [
    "type",
    "project",
    "status",
    "owner",
    "review_cadence",
    "success_metrics",
    "risk_tier",
    "autonomy_tier",
]
PROJECT_STATUSES = {"proposed", "active", "paused", "done", "killed"}


def parse_frontmatter(text: str) -> tuple[Dict[str, Any] | None, str]:
    """Tolerant YAML-ish frontmatter parser: scalars, inline and block lists."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            end = i
            break
    if end is None:
        return None, text
    fm: Dict[str, Any] = {}
    key: str | None = None
    for raw in lines[1:end]:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") or stripped == "-":
            if key is not None and isinstance(fm.get(key), list):
                item = stripped[1:].strip().strip("'\"")
                if item:
                    fm[key].append(item)
            continue
        match = re.match(r"([^:#]+):\s*(.*)$", stripped)
        if not match:
            continue
        key = match.group(1).strip().lower()
        value = match.group(2).strip()
        if not value:
            fm[key] = []  # may be filled by a block list
        elif value.startswith("[") and value.endswith("]"):
            fm[key] = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
        else:
            fm[key] = value.strip("'\"")
    return fm, "\n".join(lines[end + 1:])


def project_filename(name: str, project_code: str, note_date: str | None = None) -> str:
    return format_note_name("overview", name, note_date, project=project_code)


def render_project_page(args: argparse.Namespace) -> str:
    metrics = normalize_list(args.success_metric) or ["TBD"]
    metric_lines = "\n".join(f"  - {metric}" for metric in metrics)
    return f"""---
type: overview
project: {re.sub(r"[^A-Z0-9_-]+", "", args.project.strip().upper())}
status: {args.status}
owner: {args.owner}
review_cadence: {args.review_cadence}
success_metrics:
{metric_lines}
risk_tier: {args.risk_tier}
autonomy_tier: {args.autonomy_tier}
---

# Project: {args.name}

- Objective: {args.objective or "TBD"}
- Current next action: TBD
- Risks: TBD
- Decisions: TBD

## Context

## Milestones

## Active Tasks

## Notes
"""


def cmd_project_new(args: argparse.Namespace) -> None:
    if args.status not in PROJECT_STATUSES:
        raise SystemExit(f"Invalid status {args.status!r}; use one of: {', '.join(sorted(PROJECT_STATUSES))}")
    filename = project_filename(args.name, args.project, args.date)
    path = projects_dir() / filename
    if path.exists():
        raise SystemExit(f"Project page already exists: {path.relative_to(ROOT)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_project_page(args), encoding="utf-8")
    print(f"Created {path.relative_to(ROOT)}")


def project_page_issues(path: Path) -> List[str]:
    issues: List[str] = []
    fm, _ = parse_frontmatter(path.read_text(encoding="utf-8", errors="ignore"))
    if fm is None:
        issues.append("no frontmatter")
        fm = {}
    for field in PROJECT_REQUIRED_FIELDS:
        value = fm.get(field)
        if value is None or value == "" or value == []:
            issues.append(f"missing {field}")
    status = fm.get("status")
    if isinstance(status, str) and status and status not in PROJECT_STATUSES:
        issues.append(f"invalid status {status!r}")
    name_errors = validate_note_name(path.name)
    if name_errors:
        issues.append("filename breaks naming convention")
    return issues


def build_project_index() -> List[Dict[str, Any]]:
    root = projects_dir()
    if not root.exists():
        return []
    skip = {"Project_Template.md", "README.md"}
    pages: List[Dict[str, Any]] = []
    for path in sorted(root.glob("*.md")):
        if path.name in skip:
            continue
        pages.append({"path": path, "issues": project_page_issues(path)})
    return pages


def cmd_project_index(_: argparse.Namespace) -> None:
    pages = build_project_index()
    if not pages:
        print("No project pages found in os/04_Projects/.")
        return
    broken = 0
    for page in pages:
        rel = page["path"].relative_to(ROOT)
        if page["issues"]:
            broken += 1
            print(f"- {rel}: " + "; ".join(page["issues"]))
        else:
            print(f"- {rel}: OK")
    print(f"\n{len(pages)} project page(s); {broken} with missing fields or naming issues.")
    if broken:
        raise SystemExit(1)


def load_workflow_telemetry() -> Dict[str, Any]:
    registry = load_json(workflow_registry_path(), "workflow registry")
    telemetry = registry.get("telemetry") or {}
    return {
        "event_types": set(telemetry.get("event_types") or []),
        "statuses": set(telemetry.get("statuses") or []),
    }


def telemetry_events_file(timestamp: str) -> Path:
    return telemetry_dir() / timestamp[:7] / "events.jsonl"


def cmd_telemetry_log(args: argparse.Namespace) -> None:
    contract = load_workflow_telemetry()
    if args.event not in contract["event_types"]:
        raise SystemExit(
            f"Invalid event type {args.event!r}; allowed: " + ", ".join(sorted(contract["event_types"]))
        )
    if args.status not in contract["statuses"]:
        raise SystemExit(
            f"Invalid status {args.status!r}; allowed: " + ", ".join(sorted(contract["statuses"]))
        )
    payload = {
        "id": str(uuid.uuid4()),
        "created_at": utc_timestamp(),
        "event": args.event,
        "workflow": normalize_text(args.workflow),
        "status": args.status,
        "actor": normalize_text(args.actor),
        "task_id": normalize_text(args.task),
        "run_id": normalize_text(args.run),
        "summary": normalize_text(args.summary),
    }
    missing = [field for field in ("workflow", "actor") if not payload[field]]
    if missing:
        raise SystemExit("Missing telemetry field(s): " + ", ".join(missing))
    path = telemetry_events_file(str(payload["created_at"]))
    append_jsonl(path, payload)
    print(f"Logged {args.event} to {path.relative_to(ROOT)}")


def load_telemetry_events() -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    if not telemetry_dir().exists():
        return events
    for path in sorted(telemetry_dir().glob("*/events.jsonl")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON in {path.relative_to(ROOT)}:{line_no}: {exc}") from exc
            if isinstance(payload, dict):
                events.append(payload)
    return events


def iso_week(timestamp: str) -> str:
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    year, week, _ = parsed.isocalendar()
    return f"{year}-W{week:02d}"


def count_by(events: List[Dict[str, Any]], field: str) -> List[tuple[str, int]]:
    counts: Dict[str, int] = defaultdict(int)
    for event in events:
        counts[str(event.get(field) or "(none)")] += 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def render_telemetry_report(week: str, events: List[Dict[str, Any]]) -> str:
    lines = [
        f"# Telemetry Report: {week}",
        "",
        f"- Generated At: {utc_timestamp()}",
        f"- Events: {len(events)}",
        "",
    ]
    for field, title in (("workflow", "By Workflow"), ("status", "By Status"), ("actor", "By Actor"), ("event", "By Event Type")):
        lines += [f"## {title}", ""]
        lines += [f"- {name}: {count}" for name, count in count_by(events, field)] or ["- none"]
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def cmd_telemetry_report(args: argparse.Namespace) -> None:
    week = normalize_text(args.week) or iso_week(utc_timestamp())
    if not re.fullmatch(r"\d{4}-W\d{2}", week):
        raise SystemExit("Week must be ISO format, e.g. 2026-W24")
    events = [event for event in load_telemetry_events() if iso_week(str(event.get("created_at"))) == week]
    report = render_telemetry_report(week, events)
    path = telemetry_dir() / "reports" / f"{week}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    print(report)
    print(f"Report: {path.relative_to(ROOT)}")


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


def cmd_validate_all(_: argparse.Namespace) -> None:
    errors: List[str] = []
    errors.extend(validate_data(load()))
    for path, schema_path in control_plane_schema_targets()[1:]:
        errors.extend(validate_json_file(path, schema_path))
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("OK: control plane is valid")


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
    path = DECISIONS / format_note_name("decision", args.title, now())
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


def cmd_note_name(args: argparse.Namespace) -> None:
    if args.check:
        errors = validate_note_name(args.check)
        if errors:
            print("INVALID")
            for error in errors:
                print(f"- {error}")
            raise SystemExit(1)
        print("OK: filename follows Personal OS convention")
        return
    print(format_note_name(args.type, args.description, args.date, args.project))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(required=True)
    sub.add_parser("init").set_defaults(func=cmd_init)
    sub.add_parser("validate").set_defaults(func=cmd_validate)
    sub.add_parser("validate-all").set_defaults(func=cmd_validate_all)
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
    note = sub.add_parser("note-name")
    note.add_argument("--type", default="draft", choices=sorted(STANDARD_NOTE_TYPES))
    note.add_argument("--description", default="untitled")
    note.add_argument("--date")
    note.add_argument("--project")
    note.add_argument("--check", help="Validate an existing filename instead of formatting a new one.")
    note.set_defaults(func=cmd_note_name)
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
    run_start = sub.add_parser("run-start")
    run_start.add_argument("--task", required=True)
    run_start.add_argument("--workflow", default="task")
    run_start.add_argument("--actor", default="local-agent")
    run_start.add_argument("--run-id")
    run_start.set_defaults(func=cmd_run_start)
    run_step = sub.add_parser("run-step")
    run_step.add_argument("--run", required=True)
    run_step.add_argument("--summary", required=True)
    run_step.add_argument("--status", choices=sorted(STEP_STATUSES), default="completed")
    run_step.add_argument("--evidence", action="append")
    run_step.set_defaults(func=cmd_run_step)
    run_finish = sub.add_parser("run-finish")
    run_finish.add_argument("--run", required=True)
    run_finish.add_argument("--status", choices=sorted(RUN_FINAL_STATUSES | {"blocked"}), default="completed")
    run_finish.add_argument("--verification", default="")
    run_finish.add_argument("--evidence", action="append")
    run_finish.add_argument("--artifact", action="append")
    run_finish.add_argument("--approval-id", action="append")
    run_finish.set_defaults(func=cmd_run_finish)
    run_receipt = sub.add_parser("run-receipt")
    run_receipt.add_argument("--run", required=True)
    run_receipt.set_defaults(func=cmd_run_receipt)
    approval_request = sub.add_parser("approval-request")
    approval_request.add_argument("--id")
    approval_request.add_argument("--task-id", required=True)
    approval_request.add_argument("--requested-by", required=True)
    approval_request.add_argument("--requested-for", required=True)
    approval_request.add_argument("--policy-action", choices=sorted(POLICY_ACTIONS), required=True)
    approval_request.add_argument("--tool-scope", action="append", required=True)
    approval_request.add_argument("--summary", required=True)
    approval_request.add_argument("--risk-tier", choices=sorted(RISKS), required=True)
    approval_request.add_argument("--autonomy-tier", choices=sorted(AUTONOMY), required=True)
    approval_request.add_argument("--run-id", default="")
    approval_request.add_argument("--step-id", default="")
    approval_request.add_argument("--thread-id", default="local")
    approval_request.add_argument("--mission-id", default="local")
    approval_request.add_argument("--rationale", default="")
    approval_request.set_defaults(func=cmd_approval_request)
    approval_decide = sub.add_parser("approval-decide")
    approval_decide.add_argument("--approval", required=True)
    approval_decide.add_argument("--decision", choices=sorted(APPROVAL_DECISIONS), required=True)
    approval_decide.add_argument("--decided-by", default="")
    approval_decide.add_argument("--rationale", default="")
    approval_decide.set_defaults(func=cmd_approval_decide)
    approval_list = sub.add_parser("approval-list")
    approval_list.add_argument("--status", choices=["all", "pending", "decided"], default="pending")
    approval_list.set_defaults(func=cmd_approval_list)
    context_pack = sub.add_parser("context-pack")
    context_pack.add_argument("--task", required=True)
    context_pack.add_argument("--role", required=True)
    context_pack.set_defaults(func=cmd_context_pack)
    project_new = sub.add_parser("project-new")
    project_new.add_argument("--name", required=True)
    project_new.add_argument("--project", required=True, help="Short project code, e.g. AIMAX.")
    project_new.add_argument("--status", default="active")
    project_new.add_argument("--owner", default="user")
    project_new.add_argument("--review-cadence", dest="review_cadence", default="weekly")
    project_new.add_argument("--success-metric", action="append")
    project_new.add_argument("--risk-tier", dest="risk_tier", choices=sorted(RISKS), default="low")
    project_new.add_argument("--autonomy-tier", dest="autonomy_tier", choices=sorted(AUTONOMY), default="A1")
    project_new.add_argument("--objective", default="")
    project_new.add_argument("--date")
    project_new.set_defaults(func=cmd_project_new)
    project_index = sub.add_parser("project-index")
    project_index.set_defaults(func=cmd_project_index)
    telemetry_log = sub.add_parser("telemetry-log")
    telemetry_log.add_argument("--event", required=True)
    telemetry_log.add_argument("--workflow", required=True)
    telemetry_log.add_argument("--status", default="completed")
    telemetry_log.add_argument("--actor", required=True)
    telemetry_log.add_argument("--task", default="")
    telemetry_log.add_argument("--run", default="")
    telemetry_log.add_argument("--summary", default="")
    telemetry_log.set_defaults(func=cmd_telemetry_log)
    telemetry_report = sub.add_parser("telemetry-report")
    telemetry_report.add_argument("--week", default="", help="ISO week, e.g. 2026-W24; default: current week.")
    telemetry_report.set_defaults(func=cmd_telemetry_report)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
