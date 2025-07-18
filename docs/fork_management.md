# Fork Management Guide

This document explains how to manage your ATLAS Darwin fork, sync with upstream changes, and contribute improvements back to the main project.

## Overview

The `aiinfra-atlas-darwin` repository is a specialized fork of the main `aiinfra-atlas` project, focused on Charles Darwin's correspondence and writings. This guide covers best practices for:

- Keeping your fork synchronized with upstream improvements
- Contributing Darwin-specific enhancements
- Managing feature branches effectively
- Preparing pull requests for upstream contribution

## Quick Commands

ATLAS provides convenient Make targets for fork management:

```bash
# Check your fork's status vs upstream
make fork-status

# Sync with upstream improvements  
make fork-sync

# Create a new feature branch
make fork-feature

# Prepare a branch for pull request to upstream
make fork-pr
```

You can also call the script directly:

```bash
# Direct script usage
./utils/scripts/sync-upstream.sh status
./utils/scripts/sync-upstream.sh sync
./utils/scripts/sync-upstream.sh feature
./utils/scripts/sync-upstream.sh pr
```

## Fork Structure

### Remotes Configuration

Your fork should have two remotes configured:

- **`origin`**: Your fork (`AI-as-Infrastructure/aiinfra-atlas-darwin`)
- **`upstream`**: Original repository (`AI-as-Infrastructure/aiinfra-atlas`)

The setup script automatically configures these when you use the fork management commands.

### Branch Strategy

#### Main Branch
- Contains your stable Darwin-specific modifications
- Periodically synced with upstream improvements
- Should always be deployable

#### Feature Branches
- Created for specific enhancements or fixes
- Named descriptively (e.g., `darwin-corpus-filtering`, `fix-citation-format`)
- Based on latest upstream or your main branch as appropriate

## Common Workflows

### 1. Checking Fork Status

Before starting any work, check your fork's relationship with upstream:

```bash
make fork-status
```

This shows:
- Your current branch
- Commits in your fork not in upstream
- Commits in upstream not in your fork
- Remote configuration

### 2. Syncing with Upstream

Regularly pull in improvements from the main project:

```bash
make fork-sync
```

This process:
1. Fetches latest changes from upstream
2. Shows you what's new
3. Offers to merge upstream changes
4. Optionally pushes updates to your fork

**Best Practice**: Sync weekly or before starting new features.

### 3. Creating Feature Branches

For any new work, create a dedicated branch:

```bash
make fork-feature
# Enter branch name when prompted (e.g., "darwin-metadata-enhancement")
```

This creates and switches to a new branch based on your current branch.

### 4. Preparing Pull Requests

When ready to contribute a feature back to upstream:

```bash
# Switch to your feature branch
git checkout your-feature-branch

# Prepare for PR (rebases on latest upstream)
make fork-pr
```

This command:
1. Syncs your branch with latest upstream
2. Rebases your changes cleanly
3. Provides a GitHub link to create the pull request

## Contribution Guidelines

### Darwin-Specific vs General Improvements

**Keep in your fork:**
- Darwin corpus-specific configurations
- Darwin-themed UI customizations  
- Specialized citation formats for Darwin materials
- Darwin-specific documentation

**Contribute to upstream:**
- General bug fixes
- Performance improvements
- New LLM provider integrations
- Security enhancements
- Core feature improvements

### Commit Message Format

Use clear, descriptive commit messages:

```bash
# Good examples
git commit -m "Fix memory leak in embedding processing"
git commit -m "Add support for Google Gemini 2.0"
git commit -m "Darwin: Add specialized citation formatting"

# Less helpful
git commit -m "Fix bug"
git commit -m "Updates"
```

### Pull Request Process

1. **Create feature branch**: `make fork-feature`
2. **Implement your changes** with tests if applicable
3. **Prepare for PR**: `make fork-pr`
4. **Create PR** using the provided GitHub link
5. **Address review feedback** as needed

## Advanced Scenarios

### Handling Merge Conflicts

When syncing with upstream creates conflicts:

1. **Review conflicting files**: Git will mark conflict areas
2. **Resolve conflicts**: Edit files to combine changes appropriately
3. **Test thoroughly**: Ensure Darwin-specific features still work
4. **Commit resolution**: `git add .` and `git commit`

### Selective Cherry-Picking

To pull specific upstream commits without a full sync:

```bash
# Fetch latest upstream
git fetch upstream

# Cherry-pick specific commit
git cherry-pick <commit-hash>

# Push to your fork
git push origin main
```

### Reverting Problematic Syncs

If an upstream sync breaks Darwin functionality:

```bash
# Find the commit before the problematic sync
git log --oneline

# Reset to that commit (replace <commit-hash>)
git reset --hard <commit-hash>

# Force push to your fork (use with caution)
git push --force-with-lease origin main
```

## Monitoring Upstream Activity

### Checking for Updates

Regularly check what's happening upstream:

```bash
# See latest upstream commits
git log upstream/main --oneline -10

# Compare your main with upstream
git log HEAD..upstream/main --oneline
```

### Following Releases

Watch for upstream releases that might contain important updates:

- Monitor the [upstream repository](https://github.com/AI-as-Infrastructure/aiinfra-atlas) for release tags
- Check the release notes for breaking changes
- Test new releases with Darwin-specific features before syncing

## Troubleshooting

### Common Issues

**Remote not configured**:
```bash
# Manually add upstream remote
git remote add upstream https://github.com/AI-as-Infrastructure/aiinfra-atlas.git
```

**Merge conflicts during sync**:
- Use `git status` to see conflicted files
- Edit conflicts manually or use a merge tool
- Test Darwin features after resolving

**Fork significantly behind upstream**:
- Consider a fresh sync: `make fork-sync`
- May require manual conflict resolution
- Test thoroughly after major syncs

**Permission denied when pushing**:
- Ensure you have write access to your fork
- Check GitHub authentication: `git config --list | grep user`

### Getting Help

1. **Check logs**: Use `git log --graph --oneline --all` to visualize branch relationships
2. **Review status**: `make fork-status` provides detailed current state
3. **Test locally**: Always test Darwin features after upstream syncs
4. **Community support**: Reach out via GitHub issues for complex scenarios

## Best Practices Summary

1. **Regular syncing**: Weekly or before new features
2. **Feature branches**: Always work in branches, never directly on main
3. **Clear commits**: Descriptive messages aid future maintenance
4. **Test thoroughly**: Ensure Darwin features work after upstream changes
5. **Contribute back**: Share generally useful improvements with upstream
6. **Document changes**: Update docs when adding Darwin-specific features

This workflow ensures your Darwin fork stays current with improvements while maintaining its specialized functionality and contributing value back to the broader ATLAS ecosystem.
