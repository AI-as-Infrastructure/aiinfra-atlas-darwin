#!/bin/bash
# Darwin Fork Management Script
# Handles the significant divergence in the Darwin fork

set -e

echo "🦕 Darwin Fork Management"
echo "========================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to show Darwin-specific status
darwin_status() {
    echo -e "${BLUE}📊 Darwin Fork Status:${NC}"
    echo "=================="
    echo "Current branch: $(git branch --show-current)"
    echo
    
    echo -e "${YELLOW}🦕 Darwin-specific files:${NC}"
    echo "- create/Darwin/ (Darwin corpus processing)"
    echo "- backend/retrievers/darwin_retriever.py"
    echo "- backend/targets/darwin.txt"
    echo "- backend/targets/chroma_db/ (LFS tracked)"
    
    echo
    echo -e "${YELLOW}📁 LFS files status:${NC}"
    git lfs ls-files | head -5
    if [ $(git lfs ls-files | wc -l) -gt 5 ]; then
        echo "... and $(git lfs ls-files | wc -l) total LFS files"
    fi
    
    echo
    echo -e "${YELLOW}🔄 Commits ahead of upstream:${NC}"
    git log upstream/main..HEAD --oneline | head -10
    
    echo
    echo -e "${YELLOW}📈 Commits behind upstream:${NC}"
    git log HEAD..upstream/main --oneline | head -10
    
    echo
    echo -e "${YELLOW}⚠️  Potential conflict files:${NC}"
    # Show files that exist in both but might conflict
    git diff --name-only upstream/main HEAD | grep -E '\.(py|js|vue|txt|md)$' | head -10
}

# Function to backup Darwin files
backup_darwin() {
    local backup_name="darwin-backup-$(date +%Y%m%d-%H%M%S)"
    echo -e "${GREEN}💾 Creating Darwin backup: ${backup_name}${NC}"
    
    mkdir -p backups
    tar -czf "backups/${backup_name}.tar.gz" \
        create/Darwin/ \
        backend/retrievers/darwin_retriever.py \
        backend/targets/darwin.txt \
        backend/targets/chroma_db/ \
        .gitattributes \
        2>/dev/null || echo "Some files may not exist yet"
    
    echo "✅ Backup saved to backups/${backup_name}.tar.gz"
    return 0
}

# Function for safe upstream sync
safe_sync() {
    echo -e "${YELLOW}🔄 Safe Upstream Sync${NC}"
    echo "This will attempt to merge upstream changes while preserving Darwin features."
    echo
    
    # First, backup
    backup_darwin
    
    # Fetch upstream
    echo "Fetching upstream..."
    git fetch upstream
    
    # Show what would be merged
    echo
    echo -e "${BLUE}📋 New upstream commits:${NC}"
    git log HEAD..upstream/main --oneline | head -20
    
    echo
    read -p "Continue with merge? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Sync cancelled"
        return 1
    fi
    
    # Attempt merge
    echo "🔄 Attempting merge..."
    if git merge upstream/main --no-ff; then
        echo -e "${GREEN}✅ Merge successful!${NC}"
        echo "🧪 Please test Darwin functionality:"
        echo "  make b    # Test backend"
        echo "  make f    # Test frontend"
        echo "  make vs   # Test Darwin vector store"
    else
        echo -e "${RED}⚠️  Merge conflicts detected${NC}"
        echo "Resolve conflicts manually, then:"
        echo "  git add ."
        echo "  git commit"
        echo
        echo "Conflict resolution tips:"
        echo "- Keep Darwin-specific directories (create/Darwin/)"
        echo "- Preserve LFS configuration"
        echo "- Accept upstream improvements where compatible"
        echo "- Test thoroughly after resolution"
    fi
}

# Function to cherry-pick specific upstream commits
cherry_pick() {
    echo -e "${YELLOW}🍒 Cherry-pick Upstream Commits${NC}"
    echo
    
    # Show recent upstream commits
    echo "Recent upstream commits:"
    git log upstream/main --oneline -20 | nl
    
    echo
    read -p "Enter commit hash to cherry-pick: " commit_hash
    
    if [ -z "$commit_hash" ]; then
        echo "❌ No commit hash provided"
        return 1
    fi
    
    # Backup first
    backup_darwin
    
    echo "🍒 Cherry-picking $commit_hash..."
    if git cherry-pick "$commit_hash"; then
        echo -e "${GREEN}✅ Cherry-pick successful!${NC}"
        echo "🧪 Test Darwin functionality to ensure compatibility"
    else
        echo -e "${RED}⚠️  Cherry-pick conflicts detected${NC}"
        echo "Resolve conflicts manually, then:"
        echo "  git add ."
        echo "  git cherry-pick --continue"
    fi
}

# Function to check Darwin functionality
test_darwin() {
    echo -e "${BLUE}🧪 Testing Darwin Functionality${NC}"
    echo
    
    # Check if Darwin files exist
    local errors=0
    
    echo "Checking Darwin files..."
    if [ ! -d "create/Darwin" ]; then
        echo -e "${RED}❌ create/Darwin/ directory missing${NC}"
        ((errors++))
    else
        echo -e "${GREEN}✅ create/Darwin/ directory exists${NC}"
    fi
    
    if [ ! -f "backend/retrievers/darwin_retriever.py" ]; then
        echo -e "${RED}❌ darwin_retriever.py missing${NC}"
        ((errors++))
    else
        echo -e "${GREEN}✅ darwin_retriever.py exists${NC}"
    fi
    
    if [ ! -f "backend/targets/darwin.txt" ]; then
        echo -e "${RED}❌ darwin.txt target missing${NC}"
        ((errors++))
    else
        echo -e "${GREEN}✅ darwin.txt target exists${NC}"
    fi
    
    # Check LFS files
    echo
    echo "Checking LFS configuration..."
    if git lfs ls-files | grep -q "chroma_db"; then
        echo -e "${GREEN}✅ LFS tracking chroma_db files${NC}"
    else
        echo -e "${YELLOW}⚠️  No LFS files found for chroma_db${NC}"
    fi
    
    echo
    if [ $errors -eq 0 ]; then
        echo -e "${GREEN}✅ All Darwin components present${NC}"
        echo "💡 Run 'make vs' to test vector store creation"
        echo "💡 Run 'make r' to test retriever generation"
    else
        echo -e "${RED}❌ $errors errors found in Darwin setup${NC}"
        echo "💡 You may need to restore from backup or re-create missing files"
    fi
}

# Function to restore from backup
restore_backup() {
    echo -e "${YELLOW}📦 Restore from Backup${NC}"
    echo
    
    if [ ! -d "backups" ] || [ -z "$(ls -A backups 2>/dev/null)" ]; then
        echo "❌ No backups found"
        return 1
    fi
    
    echo "Available backups:"
    ls -la backups/*.tar.gz 2>/dev/null | nl
    
    echo
    read -p "Enter backup filename (without path): " backup_file
    
    if [ ! -f "backups/$backup_file" ]; then
        echo "❌ Backup file not found"
        return 1
    fi
    
    echo "⚠️  This will overwrite current Darwin files!"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Restore cancelled"
        return 1
    fi
    
    echo "📦 Restoring from $backup_file..."
    tar -xzf "backups/$backup_file"
    echo -e "${GREEN}✅ Restore complete${NC}"
    echo "🧪 Test Darwin functionality to ensure everything works"
}

# Function to show recommended workflow
show_workflow() {
    echo -e "${BLUE}📋 Recommended Darwin Fork Workflow${NC}"
    echo "=================================="
    echo
    echo -e "${GREEN}Daily workflow:${NC}"
    echo "1. Check status: ./utils/scripts/darwin-fork.sh status"
    echo "2. Before changes: ./utils/scripts/darwin-fork.sh backup"
    echo "3. Test after changes: ./utils/scripts/darwin-fork.sh test"
    echo
    echo -e "${YELLOW}Syncing with upstream:${NC}"
    echo "1. Backup first: ./utils/scripts/darwin-fork.sh backup"
    echo "2. Safe sync: ./utils/scripts/darwin-fork.sh sync"
    echo "3. Or cherry-pick: ./utils/scripts/darwin-fork.sh cherry-pick"
    echo "4. Test Darwin: ./utils/scripts/darwin-fork.sh test"
    echo
    echo -e "${BLUE}Your fork has significant divergence:${NC}"
    echo "- Custom Darwin corpus processing"
    echo "- LFS-managed database files"
    echo "- Modified core retrieval system"
    echo "- Darwin-specific UI components"
    echo
    echo -e "${RED}⚠️  Full upstream merges are risky!${NC}"
    echo "Use cherry-picking for safer integration of upstream improvements."
}

# Main menu
case "${1:-menu}" in
    "status")
        darwin_status
        ;;
    "backup")
        backup_darwin
        ;;
    "sync")
        safe_sync
        ;;
    "cherry-pick")
        cherry_pick
        ;;
    "test")
        test_darwin
        ;;
    "restore")
        restore_backup
        ;;
    "workflow")
        show_workflow
        ;;
    "menu"|*)
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  status       - Show Darwin fork status vs upstream"
        echo "  backup       - Backup Darwin-specific files"
        echo "  sync         - Safe upstream sync (with conflicts handling)"
        echo "  cherry-pick  - Cherry-pick specific upstream commits"
        echo "  test         - Test Darwin functionality"
        echo "  restore      - Restore from backup"
        echo "  workflow     - Show recommended workflow"
        echo
        echo "🦕 This script handles the significant divergence in your Darwin fork"
        echo "⚠️  Your fork has major differences from upstream - use carefully!"
        ;;
esac
