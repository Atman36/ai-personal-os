from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "obsidian_index.py"


def load_module():
    spec = importlib.util.spec_from_file_location("obsidian_index_under_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FULL_NOTE = """---
title: Switch to Linear
type: decision
date: 2026-03-20
status: done
project: Personal OS
tags:
  - type/decision
aliases: [linear-switch]
---

Decided after comparing tools. See [[Personal OS]] and [[Roadmap#Q2|the roadmap]].
"""

PLAIN_NOTE = """Just some text, no frontmatter.

Links: [[Personal OS]], [[Weekly Review]].
"""


class ObsidianIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name) / "vault"
        self.out = Path(self.tmp.name) / "out"
        for folder in ("Projects", "Areas", "Journal", "Здоровье", ".obsidian"):
            (self.vault / folder).mkdir(parents=True)
        (self.vault / "Projects/{decision} switch to linear – 2026-03-20.md").write_text(
            FULL_NOTE, encoding="utf-8"
        )
        (self.vault / "Projects/notes.md").write_text(PLAIN_NOTE, encoding="utf-8")
        (self.vault / "Projects/weekly review.md").write_text("# Weekly\n", encoding="utf-8")
        (self.vault / "Areas/Weekly Review.md").write_text("# Weekly too\n", encoding="utf-8")
        (self.vault / "Journal/2026-06-10.md").write_text("private diary entry", encoding="utf-8")
        (self.vault / "Здоровье/анализы.md").write_text("private health note", encoding="utf-8")
        (self.vault / ".obsidian/workspace.md").write_text("app state", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def snapshot(self) -> dict:
        return {
            str(p.relative_to(self.vault)): p.read_bytes()
            for p in self.vault.rglob("*")
            if p.is_file()
        }

    def build(self, include=None):
        return self.module.build_index(self.vault, include or [], list(self.module.DEFAULT_DENY))

    def test_denylist_skips_private_folders(self) -> None:
        index = self.build()
        paths = [note["path"] for note in index["notes"]]
        self.assertEqual(index["skipped_denied"], 2)
        self.assertFalse(any(p.startswith(("Journal/", "Здоровье/")) for p in paths))
        self.assertEqual(index["scanned"], 4)

    def test_note_without_frontmatter_does_not_crash(self) -> None:
        index = self.build()
        note = next(n for n in index["notes"] if n["path"] == "Projects/notes.md")
        self.assertFalse(note["has_frontmatter"])
        self.assertIn("no_frontmatter", note["issues"])
        self.assertIn("generic_filename", note["issues"])
        self.assertEqual(note["wikilinks"], ["Personal OS", "Weekly Review"])

    def test_frontmatter_and_filename_extraction(self) -> None:
        index = self.build()
        note = next(n for n in index["notes"] if "switch to linear" in n["path"])
        self.assertEqual(note["title"], "Switch to Linear")
        self.assertEqual(note["type"], "decision")
        self.assertEqual(note["date"], "2026-03-20")
        self.assertEqual(note["status"], "done")
        self.assertEqual(note["project"], "Personal OS")
        self.assertEqual(note["tags"], ["type/decision"])
        self.assertEqual(note["aliases"], ["linear-switch"])
        self.assertEqual(note["wikilinks"], ["Personal OS", "Roadmap"])
        self.assertTrue(note["obsidian_url"].startswith("obsidian://open?vault=vault&file="))
        self.assertEqual(note["issues"], [])

    def test_duplicates_flagged_across_folders(self) -> None:
        index = self.build()
        self.assertEqual(len(index["duplicates"]), 1)
        self.assertEqual(
            sorted(index["duplicates"][0]["paths"]),
            ["Areas/Weekly Review.md", "Projects/weekly review.md"],
        )

    def test_include_filter(self) -> None:
        index = self.build(include=["Areas"])
        self.assertEqual([n["path"] for n in index["notes"]], ["Areas/Weekly Review.md"])
        self.assertEqual(index["skipped_not_included"], 3)

    def test_run_writes_valid_outputs_and_leaves_vault_untouched(self) -> None:
        before = self.snapshot()
        self.module.run(self.vault, [], list(self.module.DEFAULT_DENY), self.out)
        index = json.loads((self.out / "index.json").read_text(encoding="utf-8"))
        report = (self.out / "report.md").read_text(encoding="utf-8")
        self.assertEqual(index["scanned"], 4)
        self.assertIn("## Next Actions", report)
        self.assertIn("Skipped By Denylist: 2", report)
        self.assertEqual(self.snapshot(), before)

    def test_refuses_output_inside_vault(self) -> None:
        with self.assertRaises(SystemExit):
            self.module.run(self.vault, [], list(self.module.DEFAULT_DENY), self.vault / "out")


if __name__ == "__main__":
    unittest.main()
