# Darwin Fork Divergence Management

## Summary of Your Situation

Your `aiinfra-atlas-darwin` fork has **significant divergence** from the upstream `aiinfra-atlas` repository:

### ✅ What You Have (Darwin-Specific)
- **Complete Darwin corpus processing**: `create/Darwin/xml/`
- **Custom Darwin retriever**: `backend/retrievers/darwin_retriever.py`
- **LFS-managed database**: `backend/targets/chroma_db/` (6 LFS files)
- **Darwin target configuration**: `backend/targets/darwin.txt`
- **Fork management tools**: Documentation and scripts
- **4 commits ahead** of upstream with custom changes

### ⚠️ Challenges
- **Core file modifications**: Your fork modifies files that upstream also changes
- **LFS complexity**: Database files managed differently than upstream
- **Large divergence**: 60+ files differ between your fork and upstream
- **Potential conflicts**: Config, retrieval, and app files likely to conflict

## Recommended Strategy: **Selective Integration**

❌ **DON'T**: Use `make fork-sync` for full merges (too risky)  
✅ **DO**: Use `make darwin-sync` for careful, tested integration

### Daily Workflow

```bash
# 1. Check your status
make darwin-status

# 2. Backup before any changes
make darwin-backup

# 3. For specific upstream improvements
./utils/scripts/darwin-fork.sh cherry-pick

# 4. Test Darwin functionality
./utils/scripts/darwin-fork.sh test
```

### Safe Upstream Integration

```bash
# Option 1: Cherry-pick specific improvements
make darwin-status  # See what's available upstream
./utils/scripts/darwin-fork.sh cherry-pick
# Enter specific commit hash when prompted

# Option 2: Attempt careful merge (with backup)
make darwin-backup
make darwin-sync
# Follow prompts, resolve conflicts manually
```

### What to Cherry-Pick vs Avoid

**✅ Safe to integrate:**
- Bug fixes in core modules
- Performance improvements
- New LLM provider support
- Security enhancements
- Documentation updates

**⚠️ Review carefully:**
- Changes to `backend/modules/config.py`
- Database/vector store modifications
- Retrieval system changes
- API endpoint modifications

**❌ Likely to conflict:**
- Changes to `create/` directory structure
- LFS configuration changes
- Database file updates
- Corpus-specific modifications

### Emergency Procedures

**If sync breaks Darwin functionality:**

```bash
# 1. Check what's broken
./utils/scripts/darwin-fork.sh test

# 2. Restore from backup
./utils/scripts/darwin-fork.sh restore

# 3. Or reset to last working state
git log --oneline  # Find last good commit
git reset --hard <commit-hash>
git push --force-with-lease origin main
```

### Contributing Back to Upstream

**Good candidates for upstream contribution:**
- General bug fixes you discover
- Performance improvements
- New LLM integrations
- Security enhancements
- UI improvements (non-Darwin specific)

**Keep in your fork:**
- Darwin corpus processing
- Darwin-specific UI themes
- Darwin retriever customizations
- LFS database configuration

### Long-term Maintenance

1. **Weekly check**: `make darwin-status`
2. **Monthly integration**: Cherry-pick useful upstream commits
3. **Quarterly review**: Consider larger upstream features
4. **Always backup**: Before any integration attempts

## Tools at Your Disposal

### Make Commands
- `make darwin-status` - Analyze divergence
- `make darwin-sync` - Careful upstream integration
- `make darwin-backup` - Backup Darwin files
- `make fork-feature` - Create feature branches for contributions

### Direct Scripts
- `./utils/scripts/darwin-fork.sh` - Full Darwin management
- `./utils/scripts/sync-upstream.sh` - General fork operations

## Key Insight

Your fork is essentially a **specialized distribution** of ATLAS focused on Darwin research. This is a legitimate and valuable approach, but requires careful maintenance to benefit from upstream improvements while preserving your Darwin-specific enhancements.

The tools provided help you:
1. **Monitor** what's happening upstream
2. **Selectively integrate** improvements
3. **Protect** your Darwin-specific work
4. **Contribute back** general improvements
5. **Recover** from problematic syncs

Your significant divergence is **manageable** with the right tools and approach!
