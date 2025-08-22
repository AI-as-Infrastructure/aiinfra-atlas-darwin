#!/bin/bash

# Requirements lock file generation script (isolated; no CUDA installs)
set -euo pipefail

REQ_IN="config/requirements.txt"
REQ_OUT="config/requirements.lock"
TMP_VENV=".venv_lock"

if [ ! -f "$REQ_IN" ]; then
    echo "❌ Error: $REQ_IN not found!"
    exit 1
fi

if ! command -v python3.10 >/dev/null 2>&1; then
    echo "❌ Error: python3.10 not found. Please install Python 3.10 and try again."
    exit 1
fi

echo "📦 Creating temporary Python 3.10 environment for lock generation..."
rm -rf "$TMP_VENV" || true
python3.10 -m venv "$TMP_VENV"

echo "🔌 Activating temporary environment..."
source "$TMP_VENV/bin/activate"
pip install --upgrade pip
echo "📥 Installing pip-tools..."
pip install pip-tools

# Force pure PyPI index; avoid any CUDA torch indexes leaking from env
export PIP_INDEX_URL="https://pypi.org/simple"
unset PIP_EXTRA_INDEX_URL || true
unset TORCH_CUDA_INDEX_URL || true

echo "🔒 Generating $REQ_OUT from $REQ_IN (CPU-only lock)..."
pip-compile --verbose "$REQ_IN" -o "$REQ_OUT"

echo "🧹 Cleaning up temporary environment..."
deactivate || true
rm -rf "$TMP_VENV"

echo "✅ Lock file generated successfully at $REQ_OUT"