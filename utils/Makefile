# Utilities Makefile
# Contains utility targets for project management

# Variables
VENV_DIR := .venv
PYTHON_VERSION := $(shell python3 --version 2>&1 | awk '{print $$2}')

# Utility Targets
.PHONY: l c pm vs r dvst torch-gpu gpul cpul

# General utilities
l: ## Generate requirements.lock file
	@./utils/scripts/generate_lock.sh

gpul: ## Generate GPU lockfile at config/requirements.gpu.lock
	@./utils/scripts/generate_gpu_lock.sh

cpul: ## Generate CPU lockfile at config/requirements.cpu.lock
	@./utils/scripts/generate_cpu_lock.sh

c: ## Check Python environment
	@./utils/scripts/check_env.sh

pm: ## Prepare embedding model for ATLAS
	@./utils/scripts/prepare_model.sh

# Darwin vector store targets
vs: ## Create Darwin vector store
	@./utils/scripts/create_darwin_store.sh

r: ## Generate Darwin retriever
	@./utils/scripts/create_darwin_retriever.sh

dvst: ## Darwin TXT not available (helpful message)
	@echo "❌ Darwin TXT vector store not available"
	@echo "💡 Darwin corpus uses XML sources. Use 'make vs' instead." 

# CUDA-enabled PyTorch bootstrap (optional convenience)
torch-gpu: ## Install CUDA-enabled PyTorch into .venv
	@bash utils/scripts/install_cuda_torch.sh