# Utilities Makefile
# Contains utility targets for project management

# Variables
VENV_DIR := .venv
PYTHON_VERSION := $(shell python3 --version 2>&1 | awk '{print $$2}')
TORCH_CUDA_INDEX_URL ?= https://download.pytorch.org/whl/cu128

# Utility Targets
.PHONY: l c pm vs vs-full vs-test r dvst torch-gpu

# General utilities
l: ## Generate requirements.lock file
	@./utils/scripts/generate_lock.sh

c: ## Check Python environment
	@./utils/scripts/check_env.sh

pm: ## Prepare embedding model for ATLAS
	@./utils/scripts/prepare_model.sh

# Darwin vector store targets
vs: vs-test ## Create Darwin vector store (defaults to test dataset for safety)

vs-full: ## Create FULL Darwin corpus vector store (~15K letters, ~65min, production-ready)
	@echo "🔥 Building FULL Darwin corpus vector store..."
	@echo "📊 Processing: ~15,000 letters with hybrid search capabilities"
	@echo "⏱️  Expected time: ~65 minutes (CPU), ~20 minutes (GPU)" 
	@echo "💾 Output: Production-ready vector store with rich metadata"
	@TORCH_CUDA_INDEX_URL=$(TORCH_CUDA_INDEX_URL) DARWIN_CORPUS_MODE=full ./utils/scripts/create_darwin_store.sh

vs-test: ## Create TEST Darwin corpus vector store (~16 letters, ~4min, for development)
	@echo "🧪 Building TEST Darwin corpus vector store..."
	@echo "📊 Processing: ~16 letters for quick testing"
	@echo "⏱️  Expected time: ~4 minutes"
	@echo "🔬 Output: Development vector store for testing features"
	@TORCH_CUDA_INDEX_URL=$(TORCH_CUDA_INDEX_URL) DARWIN_CORPUS_MODE=test ./utils/scripts/create_darwin_store.sh

r: ## Generate Darwin retriever
	@./utils/scripts/create_darwin_retriever.sh

dvst: ## Darwin TXT not available (helpful message)
	@echo "❌ Darwin TXT vector store not available"
	@echo "💡 Darwin corpus uses XML sources. Use 'make vs' instead." 

# CUDA-enabled PyTorch bootstrap (optional convenience)
torch-gpu: ## Install CUDA-enabled PyTorch into .venv
	@bash utils/scripts/install_cuda_torch.sh