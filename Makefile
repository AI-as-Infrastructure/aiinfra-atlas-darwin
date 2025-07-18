# Main Makefile
include deploy/Makefile
include deploy/help.mk
include utils/Makefile
include utils/help.mk

# Common variables
VENV_DIR := .venv
FRONTEND_DIR := frontend
BACKEND_DIR := backend

# Fork Management Targets
.PHONY: fork-status fork-sync fork-feature fork-pr darwin-status darwin-sync darwin-backup
fork-status: ## Show fork status vs upstream
	@./utils/scripts/sync-upstream.sh status

fork-sync: ## Sync with upstream changes
	@./utils/scripts/sync-upstream.sh sync

fork-feature: ## Create new feature branch (interactive)
	@./utils/scripts/sync-upstream.sh feature

fork-pr: ## Prepare current branch for pull request
	@./utils/scripts/sync-upstream.sh pr

# Darwin-specific fork management (for significant divergence)
darwin-status: ## Show Darwin fork status with divergence analysis
	@./utils/scripts/darwin-fork.sh status

darwin-sync: ## Safe upstream sync preserving Darwin features
	@./utils/scripts/darwin-fork.sh sync

darwin-backup: ## Backup Darwin-specific files
	@./utils/scripts/darwin-fork.sh backup

# Help target
.PHONY: help
help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "🔄 Fork Management:"
	@echo "  fork-status      Show fork status vs upstream"
	@echo "  fork-sync        Sync with upstream changes"
	@echo "  fork-feature     Create new feature branch"
	@echo "  fork-pr          Prepare branch for pull request"
	@echo ""
	@echo "🦕 Darwin Fork (Divergent):"
	@echo "  darwin-status    Show Darwin fork analysis"
	@echo "  darwin-sync      Safe sync preserving Darwin features"
	@echo "  darwin-backup    Backup Darwin-specific files"
	@echo ""
	@echo "📋 All Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)