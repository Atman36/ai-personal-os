#!/usr/bin/env python3
"""Deterministic pre-harness quality gate for Personal OS (Task 07).

Checks properties of osctl validation and report generation against small
public-safe fixtures in tests/fixtures/. It does NOT judge model quality and
needs no network. Run:

  python3 scripts/eval_os.py

Exit code 0 = all checks pass.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
STALE_DAYS = 7
GENERATED_MARKER = "Do not edit by hand"


def load_osctl():
    spec = importlib.util.spec_from_file_location("osctl_for_eval", ROOT / "scripts" / "osctl.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


osctl = load_osctl()


def fixture(name: str) -> Dict[str, Any]:
    path = FIXTURES / f"active-work-{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def stale_tasks(data: Dict[str, Any], stale_days: int = STALE_DAYS) -> List[str]:
    """Open tasks whose updated_at lags the queue's updated_at by >= stale_days.

    Staleness is measured against the fixture's own updated_at, not today,
    so the check stays deterministic.
    """
    reference = date.fromisoformat(data["updated_at"])
    threshold = reference - timedelta(days=stale_days)
    result = []
    for task in data.get("tasks", []):
        if task.get("column") in {"done", "backlog"}:
            continue
        updated = task.get("updated_at")
        if updated and date.fromisoformat(updated) <= threshold:
            result.append(task["id"])
    return result


Check = Callable[[], Optional[str]]


def check_fixtures_match_schema() -> Optional[str]:
    schema = json.loads(
        (ROOT / "os/05_Control_Plane/schemas/active-work.schema.json").read_text(encoding="utf-8")
    )
    for name in ("clean", "stale", "overloaded", "blocked", "decision-heavy"):
        errors = osctl.validate_against_schema(fixture(name), schema, schema)
        if errors:
            return f"fixture {name} breaks the schema: {errors[:3]}"
    return None


def check_clean_fixture_is_valid() -> Optional[str]:
    errors = osctl.validate_data(fixture("clean"))
    return f"clean fixture should validate, got: {errors}" if errors else None


def check_wip_overload_is_flagged() -> Optional[str]:
    errors = osctl.validate_data(fixture("overloaded"))
    if not any("WIP overload" in error for error in errors):
        return f"overloaded fixture must trigger a WIP overload error, got: {errors}"
    return None


def check_done_requires_completed_at() -> Optional[str]:
    data = copy.deepcopy(fixture("clean"))
    done = next(task for task in data["tasks"] if task["column"] == "done")
    done.pop("completed_at")
    errors = osctl.validate_data(data)
    if not any("completed_at" in error for error in errors):
        return f"done task without completed_at must fail validation, got: {errors}"
    return None


def check_stale_tasks_are_detected() -> Optional[str]:
    stale = stale_tasks(fixture("stale"))
    if "stale-forgotten-migration" not in stale:
        return f"stale fixture must contain a stale task, got: {stale}"
    fresh = stale_tasks(fixture("clean"))
    if fresh:
        return f"clean fixture must have no stale tasks, got: {fresh}"
    return None


def check_blocked_fixture_renders_waiting() -> Optional[str]:
    data = fixture("blocked")
    errors = osctl.validate_data(data)
    if errors:
        return f"blocked fixture should validate, got: {errors}"
    waiting = [task for task in data["tasks"] if task["column"] == "waiting"]
    if len(waiting) < 2:
        return "blocked fixture must keep at least two waiting tasks"
    board = osctl.render_board(data)
    if "## Waiting" not in board:
        return "rendered board must show the Waiting column for blocked work"
    return None


def check_decision_heavy_fixture() -> Optional[str]:
    data = fixture("decision-heavy")
    errors = osctl.validate_data(data)
    if errors:
        return f"decision-heavy fixture should validate, got: {errors}"
    decisions = [task for task in data["tasks"] if task["workflow"] == "decision"]
    if len(decisions) < 3:
        return "decision-heavy fixture must contain at least three decision tasks"
    missing = [task["id"] for task in decisions if not task.get("done_when")]
    if missing:
        return f"decision tasks must carry done_when: {missing}"
    return None


def check_board_is_generated_not_hand_edited() -> Optional[str]:
    board = osctl.render_board(fixture("clean"))
    if not board.startswith("# Task Board"):
        return "rendered board must start with the Task Board heading"
    if GENERATED_MARKER not in board:
        return f"rendered board must carry the {GENERATED_MARKER!r} marker"
    live_board = ROOT / "os/02_Planning/Task_Board.md"
    if live_board.exists() and GENERATED_MARKER not in live_board.read_text(encoding="utf-8"):
        return "live Task_Board.md is missing the generated marker — was it hand-edited?"
    return None


CHECKS: List[tuple[str, Check]] = [
    ("fixtures match active-work schema", check_fixtures_match_schema),
    ("clean queue validates", check_clean_fixture_is_valid),
    ("WIP overload is flagged", check_wip_overload_is_flagged),
    ("done tasks require completed_at", check_done_requires_completed_at),
    ("stale tasks are detected", check_stale_tasks_are_detected),
    ("blocked work renders in Waiting", check_blocked_fixture_renders_waiting),
    ("decision-heavy queue keeps decision contracts", check_decision_heavy_fixture),
    ("Task Board is generated, not hand-edited", check_board_is_generated_not_hand_edited),
]


def main() -> int:
    failures = 0
    for name, check in CHECKS:
        try:
            error = check()
        except Exception as exc:  # a crashing check is a failing check
            error = f"crashed: {exc!r}"
        if error:
            failures += 1
            print(f"FAIL {name}: {error}")
        else:
            print(f"PASS {name}")
    print(f"\n{len(CHECKS) - failures}/{len(CHECKS)} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
