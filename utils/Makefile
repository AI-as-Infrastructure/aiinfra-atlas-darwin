# Utilities Makefile
# Contains utility targets for project management

# Variables
VENV_DIR := .venv
PYTHON_VERSION := $(shell python3 --version 2>&1 | awk '{print $$2}')

# Utility Targets
.PHONY: l c pm vs r dvst

# General utilities
l: ## Generate requirements.lock file
	@./utils/scripts/generate_lock.sh

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