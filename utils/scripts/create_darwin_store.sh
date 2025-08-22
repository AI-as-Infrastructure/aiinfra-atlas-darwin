#!/bin/bash

# Darwin vector store creation script
set -e

# Hardcode the environment for development
export ENVIRONMENT=development
echo "Using ENVIRONMENT=$ENVIRONMENT"

echo "🔍 Checking environment..."

# Check if config directory exists
if [ ! -d "config" ]; then
    echo "❌ Error: config directory not found!"
    exit 1
fi

# Check if environment file exists
if [ ! -f "config/.env.development" ]; then
    echo "❌ Error: config/.env.development not found!"
    echo "💡 Please create config/.env.development with your environment variables"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Check if requirements.lock exists
if [ ! -f "config/requirements.lock" ]; then
    echo "❌ Error: config/requirements.lock not found!"
    echo "💡 Try running 'make l' first to generate the lock file"
    exit 1
fi

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip

# If the lockfile contains CUDA-specific torch wheels (+cu), install non-torch deps first,
# then install torch/vision/audio from the CUDA index without pinning the local '+cu' build.
PYTORCH_INDEX_DEFAULT="https://download.pytorch.org/whl/cu124"
PYTORCH_INDEX="${TORCH_CUDA_INDEX_URL:-$PYTORCH_INDEX_DEFAULT}"
if grep -qE '^(torch|torchvision|torchaudio)==.*\+cu' config/requirements.lock; then
    echo "🔧 Detected CUDA wheels in lockfile. Installing non-torch deps first..."
    TMP_NO_TORCH=$(mktemp)
    grep -v -E '^(torch|torchvision|torchaudio)==.*' config/requirements.lock > "$TMP_NO_TORCH"
    pip install -r "$TMP_NO_TORCH"
    rm -f "$TMP_NO_TORCH"

    echo "🧩 Installing CUDA-enabled torch stack from: $PYTORCH_INDEX"
    pip install --index-url "$PYTORCH_INDEX" torch torchvision torchaudio
else
    pip install -r config/requirements.lock
fi

# Check if Darwin store script exists
if [ ! -f "create/Darwin/xml/create_darwin_store.py" ]; then
    echo "❌ Error: create/Darwin/xml/create_darwin_store.py not found!"
    exit 1
fi

# Create Darwin vector store
echo "🔨 Creating Darwin vector store..."

# Set corpus mode (default to test for safety)
CORPUS_MODE="${DARWIN_CORPUS_MODE:-test}"
echo "📊 Corpus mode: $CORPUS_MODE"

if [ "$CORPUS_MODE" = "full" ]; then
    echo "🔥 Building FULL corpus (~15,000 letters, ~65 minutes)"
    python create/Darwin/xml/create_darwin_store.py --corpus-mode=full
elif [ "$CORPUS_MODE" = "test" ]; then
    echo "🧪 Building TEST corpus (~16 letters, ~4 minutes)"  
    python create/Darwin/xml/create_darwin_store.py --corpus-mode=test
else
    echo "❌ Error: Invalid DARWIN_CORPUS_MODE. Use 'full' or 'test'"
    exit 1
fi

echo "✅ Darwin vector store created successfully!"
echo "💡 Please commit the database directory and retriever file with Git LFS."