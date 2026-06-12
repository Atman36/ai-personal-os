from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "osctl.py"


def load_osctl():
    spec = importlib.util.spec_from_file_location("osctl_under_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OsctlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.osctl = load_osctl()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "os/05_Control_Plane/schemas").mkdir(parents=True)
        (self.root / "os/02_Planning").mkdir(parents=True)
        (self.root / "os/03_Decisions").mkdir(parents=True)

        self.osctl.ROOT = self.root
        self.osctl.ACTIVE = self.root / "os/05_Control_Plane/active-work.json"
        self.osctl.BOARD = self.root / "os/02_Planning/Task_Board.md"
        self.osctl.DECISIONS = self.root / "os/03_Decisions"
        self.osctl.RUNTIME = self.root / ".os_runtime"
        self.osctl.CONTROL_PLANE = self.root / "os/05_Control_Plane"
        self.osctl.SCHEMAS = self.root / "os/05_Control_Plane/schemas"
        self.osctl.ACTIVE_SCHEMA = self.root / "os/05_Control_Plane/schemas/active-work.schema.json"
        self.osctl.ACTIVE_SCHEMA.write_text(
            (Path(__file__).resolve().parents[1] / "os/05_Control_Plane/schemas/active-work.schema.json").read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )
        self.osctl.APPROVAL_SCHEMA = self.root / "os/05_Control_Plane/schemas/approval.schema.json"
        self.osctl.APPROVAL_SCHEMA.write_text(
            (Path(__file__).resolve().parents[1] / "os/05_Control_Plane/schemas/approval.schema.json").read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )
        repo_control_plane = Path(__file__).resolve().parents[1] / "os/05_Control_Plane"
        for registry in ("agent-registry.json", "workflow-registry.json"):
            (self.root / "os/05_Control_Plane" / registry).write_text(
                (repo_control_plane / registry).read_text(encoding="utf-8"), encoding="utf-8"
            )
        (self.root / "os/04_Projects").mkdir(parents=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def canonical_data(self) -> dict:
        return {
            "version": 1,
            "updated_at": "2026-06-11",
            "operating_mode": "personal-os-bootstrap",
            "objective": {
                "id": "bootstrap",
                "title": "Stand up Personal OS",
                "window": {"start": "2026-06-10", "target_end": "2026-06-30"},
            },
            "tasks": [
                {
                    "id": "task-1",
                    "title": "Task one",
                    "column": "this_week",
                    "project": "Personal OS Bootstrap",
                    "manager": "chief_of_staff",
                    "owner": "ai_ops_lead",
                    "accepts_result": "user",
                    "risk_tier": "low",
                    "autonomy_tier": "A1",
                    "workflow": "task",
                    "next_step": "Do the next thing.",
                    "done_when": "Done condition.",
                    "primary_update_file": "os/projects.md",
                }
            ],
        }

    def test_validate_rejects_legacy_task_fields(self) -> None:
        data = self.canonical_data()
        task = data["tasks"][0]
        task["status"] = task.pop("column")
        task["risk"] = task.pop("risk_tier")
        task["autonomy"] = task.pop("autonomy_tier")
        task["next"] = task.pop("next_step")

        errors = self.osctl.validate_data(data)

        self.assertTrue(any("schema" in error for error in errors), errors)
        self.assertTrue(any("missing column" in error for error in errors), errors)

    def test_add_task_writes_canonical_fields(self) -> None:
        data = self.canonical_data()
        data["tasks"] = []
        self.osctl.ACTIVE.write_text(json.dumps(data), encoding="utf-8")

        self.osctl.cmd_add(
            argparse.Namespace(
                title="New task",
                id="new-task",
                column="inbox",
                project="Personal OS Bootstrap",
                manager="chief_of_staff",
                owner="ai_ops_lead",
                accepts="user",
                risk_tier="medium",
                autonomy_tier="A2",
                workflow="task",
                next_step="Take the next step.",
                done_when="The task is complete.",
                primary_update_file="os/projects.md",
                support=None,
                tags=None,
            )
        )

        task = json.loads(self.osctl.ACTIVE.read_text(encoding="utf-8"))["tasks"][0]
        self.assertEqual(task["column"], "inbox")
        self.assertEqual(task["risk_tier"], "medium")
        self.assertEqual(task["autonomy_tier"], "A2")
        self.assertEqual(task["next_step"], "Take the next step.")
        self.assertNotIn("status", task)
        self.assertNotIn("risk", task)
        self.assertNotIn("autonomy", task)
        self.assertNotIn("next", task)

    def test_note_name_formatter_uses_personal_os_convention(self) -> None:
        name = self.osctl.format_note_name(
            "Research",
            "MCP Server Comparison!",
            "2026-03-18",
            project="acme",
        )

        self.assertEqual(name, "{ACME} {research} mcp server comparison – 2026-03-18.md")
        self.assertEqual(self.osctl.validate_note_name(name), [])

    def test_note_name_validator_rejects_ambiguous_names(self) -> None:
        errors = self.osctl.validate_note_name("Meeting Notes 03-24.md")

        self.assertTrue(errors)
        self.assertIn("filename must match", errors[0])

    def test_decision_uses_note_naming_convention(self) -> None:
        data = self.canonical_data()
        self.osctl.ACTIVE.write_text(json.dumps(data), encoding="utf-8")

        self.osctl.cmd_decision(
            argparse.Namespace(
                title="Choose first project",
                question="What should the OS manage first?",
                context="Bootstrap",
                option=["AI-MAX growth", "Personal productivity"],
                type="strategic",
                risk="medium",
            )
        )

        files = list(self.osctl.DECISIONS.glob("{decision} choose first project – *.md"))
        self.assertEqual(len(files), 1)

    def test_reflection_review_marks_single_observation_not_ready(self) -> None:
        self.osctl.cmd_reflection_capture(
            argparse.Namespace(
                agent="memory_steward",
                task="task-1",
                session="session-1",
                outcome="success",
                category="workflow",
                change_scope="workflow",
                summary="One observation",
                observation="A thing happened once.",
                issue="Potential process issue.",
                lesson="Consider changing the process.",
                proposed_rule="Do not promote one-off lessons.",
                issue_key="one-off",
                tag=["self-improvement"],
                evidence=["manual review"],
            )
        )

        result = self.osctl.build_reflection_review(min_observations=2, min_unique_sessions=2)

        self.assertEqual(result["total_reflections"], 1)
        self.assertEqual(result["ready_count"], 0)
        self.assertEqual(result["clusters"][0]["promotion_call"], "keep_private")

    def test_reflection_consume_removes_active_records_and_writes_receipt(self) -> None:
        for session in ("session-1", "session-2"):
            self.osctl.cmd_reflection_capture(
                argparse.Namespace(
                    agent="memory_steward",
                    task="task-1",
                    session=session,
                    outcome="success",
                    category="workflow",
                    change_scope="workflow",
                    summary="Repeated observation",
                    observation="The same issue repeated.",
                    issue="Repeatable process issue.",
                    lesson="Change the process.",
                    proposed_rule="Promote only repeated lessons.",
                    issue_key="repeat",
                    tag=[],
                    evidence=[],
                )
            )

        self.osctl.cmd_reflection_consume(argparse.Namespace(issue_key="repeat", reason="Applied validator."))

        result = self.osctl.build_reflection_review(min_observations=2, min_unique_sessions=2)
        receipts = list((self.osctl.RUNTIME / "reflections/receipts").glob("*.json"))
        self.assertEqual(result["total_reflections"], 0)
        self.assertEqual(len(receipts), 1)

    def start_run(self, run_id: str = "run-test") -> None:
        self.osctl.cmd_run_start(
            argparse.Namespace(task="task-1", workflow="task", actor="claude-code", run_id=run_id)
        )

    def finish_run(self, run_id: str = "run-test") -> None:
        self.osctl.cmd_run_finish(
            argparse.Namespace(
                run=run_id,
                status="completed",
                verification="unittest suite green",
                evidence=["python3 -m unittest discover -s tests"],
                artifact=[".os_runtime/artifacts/run-test/report.md"],
                approval_id=None,
            )
        )

    def test_run_lifecycle_start_step_finish_receipt(self) -> None:
        self.start_run()

        record_path = next((self.osctl.RUNTIME / "runs").glob("*/run-test.json"))
        self.assertTrue((self.osctl.RUNTIME / "artifacts/run-test").is_dir())

        self.osctl.cmd_run_step(
            argparse.Namespace(run="run-test", summary="Implemented the change.", status="completed", evidence=["diff reviewed"])
        )
        self.finish_run()

        record = json.loads(record_path.read_text(encoding="utf-8"))
        for field in self.osctl.RUN_REQUIRED:
            self.assertIn(field, record)
        self.assertEqual(record["status"], "completed")
        self.assertEqual(len(record["steps"]), 1)
        self.assertTrue(record["finished_at"])
        self.assertEqual(record["verification"]["summary"], "unittest suite green")
        self.assertEqual(record["artifact_paths"], [".os_runtime/artifacts/run-test/report.md"])

        self.osctl.cmd_run_receipt(argparse.Namespace(run="run-test"))
        receipt = record_path.with_name("run-test-receipt.md")
        self.assertTrue(receipt.exists())
        content = receipt.read_text(encoding="utf-8")
        self.assertIn("# Run Receipt: run-test", content)
        self.assertIn("Implemented the change.", content)

    def test_run_step_rejects_unknown_run(self) -> None:
        with self.assertRaises(SystemExit):
            self.osctl.cmd_run_step(
                argparse.Namespace(run="missing-run", summary="No run.", status="completed", evidence=None)
            )

    def test_run_step_rejects_finished_run(self) -> None:
        self.start_run()
        self.finish_run()

        with self.assertRaises(SystemExit):
            self.osctl.cmd_run_step(
                argparse.Namespace(run="run-test", summary="Too late.", status="completed", evidence=None)
            )

    def test_run_record_validation_flags_missing_required_fields(self) -> None:
        record = {"run_id": "run-x", "status": "running"}

        errors = self.osctl.validate_run_record(record)

        self.assertIn("missing task_id", errors)
        self.assertIn("missing verification", errors)

    def request_approval(self, approval_id: str = "approval-test") -> None:
        self.osctl.cmd_approval_request(
            argparse.Namespace(
                id=approval_id,
                task_id="task-1",
                requested_by="ai_ops_lead",
                requested_for="github_issue_create",
                policy_action="pause_for_founder_approval",
                tool_scope=["github:issues"],
                summary="Create a GitHub issue for task-1.",
                risk_tier="medium",
                autonomy_tier="A3",
                run_id="",
                step_id="",
                thread_id="local",
                mission_id="local",
                rationale="External write needs review.",
            )
        )

    def test_approval_request_writes_required_fields(self) -> None:
        self.request_approval()

        record_path = next((self.osctl.RUNTIME / "approvals").glob("*/approval-test.json"))
        record = json.loads(record_path.read_text(encoding="utf-8"))
        self.assertEqual(record["task_id"], "task-1")
        self.assertEqual(record["requested_by"], "ai_ops_lead")
        self.assertEqual(record["requested_for"], "github_issue_create")
        self.assertEqual(record["tool_scope"], ["github:issues"])
        self.assertEqual(record["risk_tier"], "medium")
        self.assertEqual(record["autonomy_tier"], "A3")
        self.assertEqual(record["status"], "pending")
        self.assertEqual(record["decision"], "")

    def test_approval_decide_approves_with_decided_by(self) -> None:
        self.request_approval()

        self.osctl.cmd_approval_decide(
            argparse.Namespace(approval="approval-test", decision="approved", decided_by="user", rationale="Approved.")
        )

        record_path = next((self.osctl.RUNTIME / "approvals").glob("*/approval-test.json"))
        record = json.loads(record_path.read_text(encoding="utf-8"))
        self.assertEqual(record["status"], "decided")
        self.assertEqual(record["decision"], "approved")
        self.assertEqual(record["decided_by"], "user")
        self.assertTrue(record["decided_at"])

    def test_approval_decide_rejects_without_owner_for_approval(self) -> None:
        self.request_approval()

        with self.assertRaises(SystemExit):
            self.osctl.cmd_approval_decide(
                argparse.Namespace(approval="approval-test", decision="approved", decided_by="", rationale="")
            )

    def test_approval_decide_rejects_request_without_decided_by(self) -> None:
        self.request_approval()

        self.osctl.cmd_approval_decide(
            argparse.Namespace(approval="approval-test", decision="rejected", decided_by="", rationale="Not needed.")
        )

        record_path = next((self.osctl.RUNTIME / "approvals").glob("*/approval-test.json"))
        record = json.loads(record_path.read_text(encoding="utf-8"))
        self.assertEqual(record["decision"], "rejected")
        self.assertEqual(record["decided_by"], "")

    def test_approval_list_filters_pending_records(self) -> None:
        self.request_approval("approval-pending")
        self.request_approval("approval-decided")
        self.osctl.cmd_approval_decide(
            argparse.Namespace(approval="approval-decided", decision="rejected", decided_by="", rationale="No.")
        )

        records = self.osctl.list_approvals(status="pending")

        self.assertEqual([record["id"] for _, record in records], ["approval-pending"])

    def test_context_pack_builds_sufficient_packet(self) -> None:
        self.osctl.ACTIVE.write_text(json.dumps(self.canonical_data()), encoding="utf-8")

        self.osctl.cmd_context_pack(argparse.Namespace(task="task-1", role="executor"))

        packet_path = self.osctl.RUNTIME / "context-packs/task-1/executor.md"
        self.assertTrue(packet_path.exists())
        packet = packet_path.read_text(encoding="utf-8")
        self.assertIn("# Context Packet: task-1 -> executor", packet)
        self.assertIn("## Task Contract", packet)
        self.assertIn("## Files To Read (pointers only)", packet)
        self.assertIn("## Files Not To Read", packet)
        self.assertIn("## Constraints", packet)
        self.assertIn("## Acceptance Criteria", packet)
        self.assertIn("## Return Format", packet)
        self.assertIn("Done when: Done condition.", packet)
        self.assertIn("`os/projects.md`", packet)
        self.assertIn("Private vault folders", packet)

    def test_context_pack_rejects_missing_task(self) -> None:
        self.osctl.ACTIVE.write_text(json.dumps(self.canonical_data()), encoding="utf-8")

        with self.assertRaises(SystemExit) as ctx:
            self.osctl.cmd_context_pack(argparse.Namespace(task="missing-task", role="executor"))
        self.assertIn("Task not found", str(ctx.exception))

    def test_context_pack_rejects_unknown_role(self) -> None:
        self.osctl.ACTIVE.write_text(json.dumps(self.canonical_data()), encoding="utf-8")

        with self.assertRaises(SystemExit) as ctx:
            self.osctl.cmd_context_pack(argparse.Namespace(task="task-1", role="wizard"))
        self.assertIn("Unknown role", str(ctx.exception))

    def project_args(self, **overrides) -> argparse.Namespace:
        defaults = dict(
            name="AI Max growth",
            project="aimax",
            status="active",
            owner="user",
            review_cadence="weekly",
            success_metric=["one paying customer"],
            risk_tier="low",
            autonomy_tier="A1",
            objective="Grow the demo product.",
            date="2026-06-12",
        )
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_project_new_follows_naming_convention(self) -> None:
        self.osctl.cmd_project_new(self.project_args())

        path = self.root / "os/04_Projects/{AIMAX} {overview} ai max growth – 2026-06-12.md"
        self.assertTrue(path.exists())
        self.assertEqual(self.osctl.validate_note_name(path.name), [])
        content = path.read_text(encoding="utf-8")
        self.assertIn("project: AIMAX", content)
        self.assertIn("status: active", content)
        self.assertIn("- one paying customer", content)

    def test_project_index_reports_missing_fields(self) -> None:
        self.osctl.cmd_project_new(self.project_args())
        broken = self.root / "os/04_Projects/{draft} broken page – 2026-06-12.md"
        broken.write_text("---\ntype: overview\nstatus: active\n---\n\n# Broken\n", encoding="utf-8")
        (self.root / "os/04_Projects/Project_Template.md").write_text("# template\n", encoding="utf-8")

        pages = self.osctl.build_project_index()

        by_name = {page["path"].name: page["issues"] for page in pages}
        self.assertEqual(len(pages), 2)  # template excluded
        self.assertEqual(by_name["{AIMAX} {overview} ai max growth – 2026-06-12.md"], [])
        broken_issues = by_name["{draft} broken page – 2026-06-12.md"]
        self.assertIn("missing project", broken_issues)
        self.assertIn("missing owner", broken_issues)
        self.assertIn("missing success_metrics", broken_issues)

    def telemetry_args(self, **overrides) -> argparse.Namespace:
        defaults = dict(
            event="task.completed",
            workflow="project_delivery",
            status="completed",
            actor="executor",
            task="task-1",
            run="",
            summary="Closed the task.",
        )
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_telemetry_log_rejects_unknown_event_type(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            self.osctl.cmd_telemetry_log(self.telemetry_args(event="task.exploded"))
        self.assertIn("Invalid event type", str(ctx.exception))
        self.assertFalse((self.osctl.RUNTIME / "telemetry").exists())

    def test_telemetry_log_appends_jsonl(self) -> None:
        self.osctl.cmd_telemetry_log(self.telemetry_args())
        self.osctl.cmd_telemetry_log(self.telemetry_args(event="run.started", status="running"))

        events_file = next((self.osctl.RUNTIME / "telemetry").glob("*/events.jsonl"))
        lines = [json.loads(line) for line in events_file.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0]["event"], "task.completed")
        self.assertEqual(lines[1]["status"], "running")

    def test_telemetry_report_counts_by_dimension(self) -> None:
        self.osctl.cmd_telemetry_log(self.telemetry_args())
        self.osctl.cmd_telemetry_log(self.telemetry_args(event="run.started", status="running", actor="claude-code"))
        week = self.osctl.iso_week(self.osctl.utc_timestamp())

        self.osctl.cmd_telemetry_report(argparse.Namespace(week=week))

        report = (self.osctl.RUNTIME / "telemetry/reports" / f"{week}.md").read_text(encoding="utf-8")
        self.assertIn("- Events: 2", report)
        self.assertIn("## By Workflow", report)
        self.assertIn("- project_delivery: 2", report)
        self.assertIn("## By Status", report)
        self.assertIn("## By Actor", report)
        self.assertIn("## By Event Type", report)
        self.assertIn("- task.completed: 1", report)

    def test_run_receipt_references_approval_record(self) -> None:
        self.request_approval()
        self.start_run()
        self.osctl.cmd_approval_decide(
            argparse.Namespace(approval="approval-test", decision="approved", decided_by="user", rationale="Approved.")
        )
        self.osctl.cmd_run_finish(
            argparse.Namespace(
                run="run-test",
                status="completed",
                verification="approval linked",
                evidence=[],
                artifact=[],
                approval_id=["approval-test"],
            )
        )

        self.osctl.cmd_run_receipt(argparse.Namespace(run="run-test"))

        receipt = next((self.osctl.RUNTIME / "runs").glob("*/run-test-receipt.md"))
        self.assertIn("approval-test", receipt.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
