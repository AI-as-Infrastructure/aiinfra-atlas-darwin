#!/usr/bin/env bash
set -euo pipefail

# Install CUDA-enabled PyTorch wheels into the project venv
# Defaults to CUDA 12.4 wheels; override via TORCH_CUDA_INDEX_URL
# Example: TORCH_CUDA_INDEX_URL=https://download.pytorch.org/whl/cu121

VENV_DIR=".venv"
INDEX_URL_DEFAULT="https://download.pytorch.org/whl/cu124"
INDEX_URL="${TORCH_CUDA_INDEX_URL:-$INDEX_URL_DEFAULT}"

if [ ! -d "$VENV_DIR" ]; then
  echo "[INFO] Creating virtualenv $VENV_DIR ..."
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

python - <<'PY'
import sys
print('Python:', sys.version)
PY

echo "[INFO] Upgrading pip..."
pip install --upgrade pip

# Remove any CPU-only torch packages if present
set +e
pip uninstall -y torch torchvision torchaudio 2>/dev/null
set -e

echo "[INFO] Installing CUDA-enabled PyTorch from: $INDEX_URL"
pip install --index-url "$INDEX_URL" torch torchvision torchaudio

python - <<'PY'
import torch
print('torch:', torch.__version__)
print('cuda_avail:', torch.cuda.is_available())
print('cuda_version:', torch.version.cuda)
print('device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')
PY

echo "[OK] CUDA-enabled PyTorch installed in $VENV_DIR"
