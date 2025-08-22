#!/bin/bash

# Darwin retriever generation script
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
    if ! command -v python3.10 >/dev/null 2>&1; then
        echo "❌ Error: python3.10 not found. Please install Python 3.10 first."
        exit 1
    fi
    python3.10 -m venv .venv
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

# Install dependencies (CPU-only)
echo "📥 Installing dependencies (CPU-only)..."
pip install --upgrade pip
export PIP_INDEX_URL="https://pypi.org/simple"
unset PIP_EXTRA_INDEX_URL || true
pip install -r config/requirements.lock

# Check if Darwin retriever script exists
if [ ! -f "create/Darwin/xml/create_darwin_retriever.py" ]; then
    echo "❌ Error: create/Darwin/xml/create_darwin_retriever.py not found!"
    exit 1
fi

# Generate Darwin retriever
echo "🔨 Generating Darwin retriever..."
python create/Darwin/xml/create_darwin_retriever.py

echo "✅ Darwin retriever generated successfully!"
echo "💡 The retriever is now ready for use with ATLAS."