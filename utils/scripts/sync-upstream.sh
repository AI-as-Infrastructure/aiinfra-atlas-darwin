#!/bin/bash
# Fork Management Script for aiinfra-atlas-darwin

set -e

echo "🔄 Fork Management Script"
echo "========================="

# Function to show current status
show_status() {
    echo
    echo "📊 Current Status:"
    echo "=================="
    echo "Current branch: $(git branch --show-current)"
    echo "Remotes:"
    git remote -v
    echo
    echo "Recent commits in your fork not in upstream:"
    git log upstream/main..HEAD --oneline || echo "None"
    echo
    echo "Recent commits in upstream not in your fork:"
    git log HEAD..upstream/main --oneline || echo "None"
}

# Function to sync with upstream
sync_upstream() {
    echo "🔄 Syncing with upstream..."
    
    # Fetch latest from upstream
    git fetch upstream
    
    # Show what's new
    echo "New commits in upstream:"
    git log HEAD..upstream/main --oneline
    
    # Ask user if they want to merge
    read -p "Do you want to merge upstream changes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Merging upstream/main into your main branch..."
        git merge upstream/main
        echo "✅ Sync complete!"
        
        # Push to your fork
        read -p "Push changes to your fork? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git push origin main
            echo "✅ Pushed to your fork!"
        fi
    else
        echo "❌ Sync cancelled"
    fi
}

# Function to create a new feature branch
new_feature_branch() {
    read -p "Enter feature branch name: " branch_name
    if [ -z "$branch_name" ]; then
        echo "❌ Branch name cannot be empty"
        return 1
    fi
    
    echo "Creating feature branch: $branch_name"
    git checkout -b "$branch_name"
    echo "✅ Created and switched to branch: $branch_name"
}

# Function to prepare for pull request
prepare_pr() {
    echo "🚀 Preparing for Pull Request..."
    current_branch=$(git branch --show-current)
    
    if [ "$current_branch" = "main" ]; then
        echo "❌ You're on main branch. Create a feature branch first."
        return 1
    fi
    
    # Sync feature branch with latest upstream
    echo "Syncing $current_branch with upstream..."
    git fetch upstream
    git rebase upstream/main
    
    echo "✅ Branch $current_branch is ready for PR"
    echo "🌐 Create PR at: https://github.com/AI-as-Infrastructure/aiinfra-atlas/compare/main...AI-as-Infrastructure:aiinfra-atlas-darwin:$current_branch"
}

# Main menu
case "${1:-menu}" in
    "status")
        show_status
        ;;
    "sync")
        sync_upstream
        ;;
    "feature")
        new_feature_branch
        ;;
    "pr")
        prepare_pr
        ;;
    "menu"|*)
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  status   - Show current fork status"
        echo "  sync     - Sync with upstream changes"
        echo "  feature  - Create new feature branch"
        echo "  pr       - Prepare current branch for pull request"
        echo
        echo "Or run without arguments for this menu"
        ;;
esac
