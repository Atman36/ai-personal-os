#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/osctl.py init
python3 scripts/osctl.py validate
python3 scripts/osctl.py sync

cat <<'MSG'
Personal OS starter is ready.

Next:
  1. Open this folder in Codex.
  2. Run: Открой $personal-os-gateway и проведи daily start.
  3. For subagents, ask explicitly: Spawn chief_of_staff and ai_ops_lead to review current work.
MSG
