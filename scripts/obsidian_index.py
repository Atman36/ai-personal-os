#!/usr/bin/env python3
"""Read-only Obsidian vault indexer for Personal OS.

Scans selected folders of an Obsidian vault, extracts note metadata
(frontmatter, naming-convention fields, wiki-links) and writes:
  .os_runtime/obsidian/index.json   machine-readable index
  .os_runtime/obsidian/report.md    note-quality report with next actions

Never writes into the vault. Private folders (diary/journal/health/therapy/
private/messages and Russian equivalents) are denied by default; remove a
token explicitly with --allow if the user opts a folder in.

No external dependencies. Usage:
  OBSIDIAN_VAULT=~/vault python3 scripts/obsidian_index.py
  python3 scripts/obsidian_index.py --vault ~/vault --include Projects --include Areas
"""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.parse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / ".os_runtime/obsidian"

# Matched as substrings against lowercased folder names. Deny wins over
# --include; the only way past it is an explicit --allow <token>.
DEFAULT_DENY = [
    "diary", "journal", "health", "therapy", "private", "messages",
    "дневник", "журнал", "здоровье", "терапия", "приват", "личное",
    "переписк", "сообщени",
]

GENERIC_NAMES = {
    "notes", "note", "untitled", "new note", "todo", "misc", "temp",
    "scratch", "draft", "заметка", "заметки", "без названия", "разное",
    "идеи", "новая заметка",
}

CURLY_RE = re.compile(r"\{([^}]+)\}")
DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
WIKILINK_RE = re.compile(r"\[\[([^\[\]]+)\]\]")
NOTE_NAME_RE = re.compile(
    r"^(?:\{(?P<project>[A-Z0-9][A-Z0-9_-]*)\} )?"
    r"\{(?P<type>[a-z][a-z0-9_-]*)\} "
    r"(?P<description>.+) – (?P<date>\d{4}-\d{2}-\d{2})$"
)


def filename_convention_errors(stem: str) -> List[str]:
    """Check the Personal OS note filename shape without requiring frontmatter."""
    match = NOTE_NAME_RE.match(stem)
    if not match:
        return ["invalid_filename_format"]
    description = match.group("description")
    if description != description.lower() or re.search(r"[^0-9a-zа-яё ]", description, flags=re.I):
        return ["invalid_filename_format"]
    return []


def parse_frontmatter(text: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Tolerant YAML-ish frontmatter parser: scalars, inline and block lists.

    Returns (frontmatter or None, body). Never raises on malformed input.
    """
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
    key: Optional[str] = None
    for raw in lines[1:end]:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") or stripped == "-":
            if key is not None:
                item = stripped[1:].strip().strip("'\"")
                if item and isinstance(fm.get(key), list):
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


def as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    return [text] if text else []


def as_text(value: Any) -> Optional[str]:
    if value is None or isinstance(value, list):
        return None
    text = str(value).strip()
    return text or None


def extract_date(value: Any) -> Optional[str]:
    match = DATE_RE.search(str(value or ""))
    return match.group(1) if match else None


def clean_title(stem: str) -> str:
    title = CURLY_RE.sub("", stem)
    title = DATE_RE.sub("", title)
    title = title.strip(" -–—_")
    return re.sub(r"\s+", " ", title).strip() or stem


def normalized_title(title: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9а-яё ]", "", title.lower())).strip()


def denied_token(rel_parts: Tuple[str, ...], deny: List[str]) -> Optional[str]:
    for part in rel_parts[:-1]:  # folders only, not the filename
        low = part.lower()
        for token in deny:
            if token in low:
                return token
    return None


def obsidian_url(vault_name: str, rel_path: str) -> str:
    file_ref = rel_path[:-3] if rel_path.endswith(".md") else rel_path
    return (
        "obsidian://open?vault=" + urllib.parse.quote(vault_name)
        + "&file=" + urllib.parse.quote(file_ref)
    )


def parse_note(path: Path, rel_path: str, vault_name: str) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    fm, body = parse_frontmatter(text)
    stem = path.stem
    curly = CURLY_RE.findall(stem)
    fname_type = curly[-1].lower() if curly else None
    fname_project = curly[0] if len(curly) >= 2 else None

    note_type = as_text((fm or {}).get("type")) or fname_type
    note_date = extract_date((fm or {}).get("date")) or extract_date(stem)
    title = as_text((fm or {}).get("title")) or clean_title(stem)

    wikilinks: List[str] = []
    for raw in WIKILINK_RE.findall(body):
        target = raw.split("|")[0].split("#")[0].strip()
        if target:
            wikilinks.append(target)

    issues: List[str] = []
    if fm is None:
        issues.append("no_frontmatter")
    if not note_type:
        issues.append("no_type")
    if not note_date:
        issues.append("no_date")
    if normalized_title(clean_title(stem)) in GENERIC_NAMES:
        issues.append("generic_filename")
    issues.extend(filename_convention_errors(stem))

    return {
        "path": rel_path,
        "title": title,
        "type": note_type,
        "date": note_date,
        "tags": as_list((fm or {}).get("tags")),
        "aliases": as_list((fm or {}).get("aliases")),
        "status": as_text((fm or {}).get("status")),
        "project": as_text((fm or {}).get("project")) or fname_project,
        "has_frontmatter": fm is not None,
        "wikilinks": wikilinks,
        "obsidian_url": obsidian_url(vault_name, rel_path),
        "issues": issues,
    }


def build_index(vault: Path, include: List[str], deny: List[str]) -> Dict[str, Any]:
    vault = vault.resolve()
    if not vault.is_dir():
        raise SystemExit(f"Vault not found: {vault}")
    includes = [inc.strip("/").replace("\\", "/") for inc in include if inc.strip("/")]
    notes: List[Dict[str, Any]] = []
    skipped_denied = 0
    skipped_not_included = 0
    for path in sorted(vault.rglob("*.md")):
        rel = path.relative_to(vault)
        if any(part.startswith(".") for part in rel.parts):
            continue  # .obsidian, .trash, etc.
        rel_posix = rel.as_posix()
        if denied_token(rel.parts, deny):
            skipped_denied += 1
            continue
        if includes and not any(
            rel_posix == inc or rel_posix.startswith(inc + "/") for inc in includes
        ):
            skipped_not_included += 1
            continue
        notes.append(parse_note(path, rel_posix, vault.name))

    by_title: Dict[str, List[Dict[str, Any]]] = {}
    for note in notes:
        key = normalized_title(note["title"])
        if key:
            by_title.setdefault(key, []).append(note)
    duplicates = []
    for key, group in sorted(by_title.items()):
        if len(group) > 1:
            duplicates.append({"title": group[0]["title"], "paths": [n["path"] for n in group]})
            for note in group:
                note["issues"].append("possible_duplicate")

    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "vault": str(vault),
        "vault_name": vault.name,
        "include": includes,
        "deny": sorted(deny),
        "scanned": len(notes),
        "skipped_denied": skipped_denied,
        "skipped_not_included": skipped_not_included,
        "duplicates": duplicates,
        "notes": notes,
    }


def breakdown(notes: List[Dict[str, Any]], field: str) -> List[Tuple[str, int]]:
    counts = Counter(str(note.get(field) or "(none)") for note in notes)
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def issue_paths(notes: List[Dict[str, Any]], issue: str) -> List[str]:
    return [note["path"] for note in notes if issue in note["issues"]]


def listing(paths: List[str], cap: int = 20) -> List[str]:
    lines = [f"- `{p}`" for p in paths[:cap]]
    if len(paths) > cap:
        lines.append(f"- … and {len(paths) - cap} more")
    return lines


def render_report(index: Dict[str, Any]) -> str:
    notes = index["notes"]
    lines = [
        "# Obsidian Vault Report",
        "",
        f"- Generated At: {index['generated_at']}",
        f"- Vault: `{index['vault']}`",
        f"- Included Folders: {', '.join(index['include']) or 'all (minus denylist)'}",
        f"- Notes Scanned: {index['scanned']}",
        f"- Skipped By Denylist: {index['skipped_denied']}",
        f"- Skipped Outside Include List: {index['skipped_not_included']}",
        "",
    ]
    for field, title in (("type", "By Type"), ("project", "By Project"), ("status", "By Status")):
        lines += [f"## {title}", ""]
        lines += [f"- {name}: {count}" for name, count in breakdown(notes, field)] or ["- (no notes)"]
        lines.append("")

    problem_sections = [
        ("no_frontmatter", "Notes Without Frontmatter"),
        ("no_type", "Notes Without Type"),
        ("no_date", "Notes Without Date"),
        ("generic_filename", "Generic Filenames"),
        ("invalid_filename_format", "Invalid Personal OS Filenames"),
    ]
    problems: Dict[str, List[str]] = {}
    for issue, title in problem_sections:
        paths = issue_paths(notes, issue)
        problems[issue] = paths
        lines += [f"## {title} ({len(paths)})", ""]
        lines += listing(paths) or ["- none"]
        lines.append("")

    lines += [f"## Possible Duplicates ({len(index['duplicates'])})", ""]
    if index["duplicates"]:
        for dup in index["duplicates"]:
            lines.append(f"- {dup['title']}: " + ", ".join(f"`{p}`" for p in dup["paths"]))
    else:
        lines.append("- none")
    lines.append("")

    link_counts = Counter(link for note in notes for link in note["wikilinks"])
    lines += ["## Top Wiki-Links", ""]
    top = link_counts.most_common(10)
    lines += [f"- [[{name}]] — {count}" for name, count in top] or ["- none"]
    lines.append("")

    lines += ["## Next Actions", ""]
    actions = []
    if problems["no_frontmatter"]:
        actions.append(
            f"Add YAML frontmatter (type, date, tags) to {len(problems['no_frontmatter'])} note(s) without it."
        )
    if problems["no_type"]:
        actions.append(
            f"Adopt the `{{type}} description – YYYY-MM-DD.md` naming convention: {len(problems['no_type'])} note(s) have no type."
        )
    if problems["no_date"]:
        actions.append(f"Add a date (frontmatter or filename) to {len(problems['no_date'])} note(s).")
    if problems["generic_filename"]:
        actions.append(f"Rename {len(problems['generic_filename'])} note(s) with generic filenames.")
    if problems["invalid_filename_format"]:
        actions.append(
            f"Rename {len(problems['invalid_filename_format'])} note(s) to `{{type}} description – YYYY-MM-DD.md`."
        )
    if index["duplicates"]:
        actions.append(f"Review and merge {len(index['duplicates'])} possible duplicate group(s).")
    if not actions:
        actions.append("Vault metadata looks healthy — no cleanup needed.")
    lines += [f"{i}. {action}" for i, action in enumerate(actions, 1)]
    return "\n".join(lines).rstrip() + "\n"


def run(vault: Path, include: List[str], deny: List[str], out: Path) -> Dict[str, Any]:
    index = build_index(vault, include, deny)
    out = out.resolve()
    if out == Path(index["vault"]) or Path(index["vault"]) in out.parents:
        raise SystemExit("Refusing to write output inside the vault (read-only contract).")
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "report.md").write_text(render_report(index), encoding="utf-8")
    return index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--vault", default=os.environ.get("OBSIDIAN_VAULT"),
                        help="Vault root (or set OBSIDIAN_VAULT)")
    parser.add_argument("--include", action="append", default=[],
                        help="Folder to index, relative to vault root; repeatable. Default: whole vault minus denylist.")
    parser.add_argument("--deny", action="append", default=[],
                        help="Extra denylist token (substring match on folder names); repeatable.")
    parser.add_argument("--allow", action="append", default=[],
                        help="Remove a default denylist token (explicit opt-in); repeatable.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help=f"Output directory (default: {DEFAULT_OUT.relative_to(ROOT)})")
    args = parser.parse_args()
    if not args.vault:
        raise SystemExit("Set --vault or OBSIDIAN_VAULT to the vault root.")
    allow = {token.lower() for token in args.allow}
    deny = [t for t in DEFAULT_DENY if t not in allow] + [t.lower() for t in args.deny]
    index = run(Path(args.vault).expanduser(), args.include, deny, args.out)
    out = args.out.resolve()
    print(f"Scanned {index['scanned']} note(s); denied {index['skipped_denied']}; "
          f"outside include list {index['skipped_not_included']}.")
    for name in ("index.json", "report.md"):
        path = out / name
        print(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


if __name__ == "__main__":
    main()
