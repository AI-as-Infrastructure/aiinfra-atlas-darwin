#!/usr/bin/env bash
set -euo pipefail

# Generate CPU requirements lockfile at config/requirements.cpu.lock
# Uses a temporary virtualenv to avoid polluting the main .venv

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

TMP_VENV=".venv_lock_cpu"
REQ_TXT="config/requirements.txt"
OUT_LOCK="config/requirements.lock"

if [ ! -f "$REQ_TXT" ]; then
  echo "[ERROR] $REQ_TXT not found" >&2
  exit 1
fi

rm -rf "$TMP_VENV" || true
python3 -m venv "$TMP_VENV"

"$TMP_VENV/bin/pip" install --upgrade pip
"$TMP_VENV/bin/pip" install -r "$REQ_TXT"

# Freeze full environment
"$TMP_VENV/bin/pip" freeze > "$OUT_LOCK"

echo "[OK] CPU lockfile written to $OUT_LOCK"

# Cleanup
rm -rf "$TMP_VENV"
