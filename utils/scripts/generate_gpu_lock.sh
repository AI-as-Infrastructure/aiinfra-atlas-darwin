#!/usr/bin/env bash
set -euo pipefail

# Generate GPU requirements lockfile at config/requirements.gpu.lock
# Installs CUDA-enabled PyTorch wheels in a temporary venv for accurate freeze

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

TMP_VENV=".venv_lock_gpu"
REQ_TXT="config/requirements.txt"
OUT_LOCK="config/requirements.lock"

# Default to CUDA 12.4 wheel index; allow override via TORCH_CUDA_INDEX_URL
INDEX_URL_DEFAULT="https://download.pytorch.org/whl/cu124"
INDEX_URL="${TORCH_CUDA_INDEX_URL:-$INDEX_URL_DEFAULT}"

if [ ! -f "$REQ_TXT" ]; then
  echo "[ERROR] $REQ_TXT not found" >&2
  exit 1
fi

rm -rf "$TMP_VENV" || true
python3 -m venv "$TMP_VENV"

"$TMP_VENV/bin/pip" install --upgrade pip

# First install all non-torch deps
# We will remove torch from the requirements install and add it via CUDA index
# to ensure GPU wheels get picked.

# Create a temp requirements without torch/torchvision/torchaudio pins
TMP_REQ="$TMP_VENV/tmp.requirements.txt"
grep -v -E '^(torch|torchvision|torchaudio)($|==|>=|<=|~=)' "$REQ_TXT" > "$TMP_REQ"

"$TMP_VENV/bin/pip" install -r "$TMP_REQ"

# Now install CUDA-enabled torch stack
"$TMP_VENV/bin/pip" install --index-url "$INDEX_URL" torch torchvision torchaudio

# Freeze full environment
"$TMP_VENV/bin/pip" freeze > "$OUT_LOCK"

echo "[OK] GPU lockfile written to $OUT_LOCK"

# Cleanup
rm -rf "$TMP_VENV"
