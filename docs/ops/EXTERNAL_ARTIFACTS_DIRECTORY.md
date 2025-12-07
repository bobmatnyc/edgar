# External Artifacts Directory Guide

**Feature**: Store projects and outputs outside the repository
**Environment Variable**: `EDGAR_ARTIFACTS_DIR`
**Status**: ✅ Production Ready

---

## Quick Start

### Set External Directory

```bash
# Set environment variable (one-time setup)
export EDGAR_ARTIFACTS_DIR=~/edgar_artifacts

# Or add to your shell profile for persistence
echo 'export EDGAR_ARTIFACTS_DIR=~/edgar_artifacts' >> ~/.bashrc
```

### Verify Configuration

```bash
# Check current artifacts directory
python -c 'from edgar_analyzer.config.settings import get_artifacts_dir; print(get_artifacts_dir())'

# Create directory structure
python -c 'from edgar_analyzer.config.settings import ensure_artifacts_structure; ensure_artifacts_structure()'

# List created directories
ls -la $EDGAR_ARTIFACTS_DIR/
# Should show: projects/ output/ data/ data/cache/ logs/
```

---

## Why Use External Artifacts Directory?

### Benefits

1. **Keep repo clean**: Projects and outputs don't clutter git status
2. **Centralized storage**: All projects in one place
3. **Easier backups**: Back up one directory instead of scattered files
4. **Team collaboration**: Share artifacts directory with team
5. **Disk management**: Store large artifacts on separate drive

### Default vs External

| Aspect | Default (In-Repo) | External Directory |
|--------|-------------------|-------------------|
| **Location** | `./projects/` | `$EDGAR_ARTIFACTS_DIR/projects/` |
| **Git Status** | Shows in `git status` | Not tracked by git |
| **Setup** | No setup needed | Set env var once |
| **Portability** | High (self-contained) | Medium (env-dependent) |
| **Use Case** | Quick tests, demos | Production, long-term |

---

## Configuration Options

### Option 1: Environment Variable (Recommended)

**Temporary** (current session only):
```bash
export EDGAR_ARTIFACTS_DIR=~/edgar_artifacts
```

**Permanent** (add to shell profile):
```bash
# For bash
echo 'export EDGAR_ARTIFACTS_DIR=~/edgar_artifacts' >> ~/.bashrc

# For zsh
echo 'export EDGAR_ARTIFACTS_DIR=~/edgar_artifacts' >> ~/.zshrc

# Then reload
source ~/.bashrc  # or source ~/.zshrc
```

### Option 2: Per-Command Override

```bash
# Set for single command
EDGAR_ARTIFACTS_DIR=/tmp/test edgar-analyzer project create test-project
```

### Option 3: .env.local File (Future)

**Note**: Requires python-dotenv configuration (planned for future release)

```bash
# Create .env.local in project root
echo 'EDGAR_ARTIFACTS_DIR=~/edgar_artifacts' > .env.local

# Then use normally
edgar-analyzer project create my-project
```

---

## Path Specifications

### Absolute Path

```bash
# Linux/macOS
export EDGAR_ARTIFACTS_DIR=/var/edgar/artifacts

# macOS (external drive)
export EDGAR_ARTIFACTS_DIR=/Volumes/External/edgar_artifacts

# Windows (future support)
export EDGAR_ARTIFACTS_DIR=C:\Edgar\Artifacts
```

### Relative Path

**Note**: Resolves relative to current working directory

```bash
# Relative to project root
export EDGAR_ARTIFACTS_DIR=./my_artifacts

# Resolves to absolute path automatically
# Example: /Users/you/projects/edgar/my_artifacts
```

### Home Directory (~)

```bash
# Tilde expansion supported
export EDGAR_ARTIFACTS_DIR=~/edgar_artifacts

# Expands to: /Users/you/edgar_artifacts (macOS)
# Expands to: /home/you/edgar_artifacts (Linux)
```

### Paths with Spaces

```bash
# Works with spaces (no quotes needed)
export EDGAR_ARTIFACTS_DIR=~/My Edgar Projects
```

---

## Directory Structure

When `EDGAR_ARTIFACTS_DIR` is set, the following structure is created:

```
$EDGAR_ARTIFACTS_DIR/
├── projects/           # Project workspace directories
│   ├── weather_api/    # Example: Weather API project
│   ├── employee_roster/ # Example: Employee roster project
│   └── my_project/     # Your projects
├── output/             # Generated reports and results
│   ├── reports/
│   └── exports/
├── data/               # Data files and cache
│   ├── cache/          # API response cache
│   └── companies/      # Company data
└── logs/               # Application logs
    └── edgar_analyzer.log
```

### Without External Directory

Default in-repo structure (when `EDGAR_ARTIFACTS_DIR` is not set):

```
edgar/                  # Project root
├── projects/           # Same structure, in repo
├── output/
├── data/
└── logs/
```

---

## Usage Examples

### Example 1: Create Project in External Directory

```bash
# Set external directory
export EDGAR_ARTIFACTS_DIR=~/edgar_artifacts

# Create project (goes to ~/edgar_artifacts/projects/)
edgar-analyzer project create weather-test --template weather

# Verify location
ls -la ~/edgar_artifacts/projects/weather-test/
```

### Example 2: Run Analysis with External Output

```bash
# Set external directory
export EDGAR_ARTIFACTS_DIR=/mnt/shared/team-artifacts

# Run analysis (outputs to /mnt/shared/team-artifacts/output/)
edgar-analyzer extract --cik 0000320193 --year 2023

# Check results
ls -la /mnt/shared/team-artifacts/output/
```

### Example 3: Multiple Projects

```bash
# Set external directory
export EDGAR_ARTIFACTS_DIR=~/my_projects

# Create multiple projects
edgar-analyzer project create project-a --template excel
edgar-analyzer project create project-b --template pdf
edgar-analyzer project create project-c --template weather

# All projects in one place
ls -la ~/my_projects/projects/
# project-a/ project-b/ project-c/
```

### Example 4: Team Collaboration

```bash
# Team shared directory
export EDGAR_ARTIFACTS_DIR=/mnt/nfs/team-edgar

# Team member 1 creates project
edgar-analyzer project create shared-analysis

# Team member 2 runs analysis
edgar-analyzer analyze-project /mnt/nfs/team-edgar/projects/shared-analysis

# Results available to entire team
```

---

## Verification & Debugging

### Check Configuration

```bash
# Show current artifacts directory
python -c 'from edgar_analyzer.config.settings import get_artifacts_dir; print(get_artifacts_dir())'

# Show ConfigService settings
python -c '
from edgar_analyzer.config.settings import ConfigService
config = ConfigService()
print(f"Artifacts base: {config.settings.artifacts_base_dir}")
print(f"Projects dir: {config.settings.get_absolute_path(\"projects\")}")
print(f"Output dir: {config.settings.get_absolute_path(\"output\")}")
'
```

### Verify Directory Creation

```bash
# Ensure structure exists
python -c 'from edgar_analyzer.config.settings import ensure_artifacts_structure; ensure_artifacts_structure()'

# Check directories
ls -la $EDGAR_ARTIFACTS_DIR/
```

### Test Path Resolution

```bash
# Test with temporary directory
export EDGAR_ARTIFACTS_DIR=/tmp/test_artifacts
python -c 'from edgar_analyzer.config.settings import ensure_artifacts_structure; ensure_artifacts_structure()'
tree /tmp/test_artifacts/
```

---

## Troubleshooting

### Issue 1: Permission Denied

**Symptom**: `Cannot create artifacts directory: Permission denied`

**Solution**:
```bash
# Check permissions
ls -ld $EDGAR_ARTIFACTS_DIR

# Fix permissions
chmod 755 $EDGAR_ARTIFACTS_DIR

# Or use different directory
export EDGAR_ARTIFACTS_DIR=~/edgar_artifacts  # Your home directory
```

### Issue 2: Directory Not Found

**Symptom**: Parent directory doesn't exist

**Solution**: Parent directories are auto-created, but base must be accessible
```bash
# Ensure parent exists
mkdir -p ~/my_projects

# Then set
export EDGAR_ARTIFACTS_DIR=~/my_projects/edgar
```

### Issue 3: Path Not Expanded

**Symptom**: `~` not expanded to home directory

**Solution**: Check shell configuration
```bash
# Test expansion
echo $EDGAR_ARTIFACTS_DIR

# Should show: /Users/you/edgar_artifacts
# Not: ~/edgar_artifacts

# If not expanded, manually set
export EDGAR_ARTIFACTS_DIR="$HOME/edgar_artifacts"
```

### Issue 4: Changes Not Applied

**Symptom**: Still using old directory

**Solution**: Restart Python/CLI
```bash
# Exit and restart Python session
# Or source venv again
source venv/bin/activate
```

---

## Best Practices

### 1. Use Absolute Paths for Production

```bash
# Good: Absolute path
export EDGAR_ARTIFACTS_DIR=/var/edgar/artifacts

# Avoid: Relative path (context-dependent)
export EDGAR_ARTIFACTS_DIR=./artifacts
```

### 2. Add to Shell Profile

```bash
# One-time setup in ~/.bashrc or ~/.zshrc
export EDGAR_ARTIFACTS_DIR=~/edgar_artifacts
```

### 3. Document Team Configuration

```markdown
# Team Setup
All team members should set:
export EDGAR_ARTIFACTS_DIR=/mnt/shared/team-edgar
```

### 4. Backup External Directory

```bash
# Regular backups
rsync -av ~/edgar_artifacts/ ~/edgar_artifacts_backup/

# Or use time machine / cloud backup
```

### 5. Verify Before Long Operations

```bash
# Always verify before large analysis
python -c 'from edgar_analyzer.config.settings import get_artifacts_dir; print(get_artifacts_dir())'
# Ensure output goes where expected
```

---

## Migration Guide

### Migrating Existing Projects to External Directory

```bash
# Step 1: Set external directory
export EDGAR_ARTIFACTS_DIR=~/edgar_artifacts

# Step 2: Create structure
python -c 'from edgar_analyzer.config.settings import ensure_artifacts_structure; ensure_artifacts_structure()'

# Step 3: Move existing projects
mv ./projects/* ~/edgar_artifacts/projects/

# Step 4: Move existing outputs
mv ./output/* ~/edgar_artifacts/output/

# Step 5: Verify
ls -la ~/edgar_artifacts/projects/
ls -la ~/edgar_artifacts/output/
```

### Reverting to In-Repo

```bash
# Step 1: Move projects back
mv $EDGAR_ARTIFACTS_DIR/projects/* ./projects/

# Step 2: Unset environment variable
unset EDGAR_ARTIFACTS_DIR

# Step 3: Verify
python -c 'from edgar_analyzer.config.settings import get_artifacts_dir; print(get_artifacts_dir())'
# Should show project root
```

---

## Advanced Usage

### Per-Project Artifacts Directory

```bash
# Create project-specific script
cat > run_project_a.sh <<'EOF'
#!/bin/bash
export EDGAR_ARTIFACTS_DIR=~/projects/project_a_artifacts
edgar-analyzer project create project-a --template weather
EOF

chmod +x run_project_a.sh
./run_project_a.sh
```

### Conditional Setup

```bash
# In ~/.bashrc - only set if not already set
if [ -z "$EDGAR_ARTIFACTS_DIR" ]; then
    export EDGAR_ARTIFACTS_DIR=~/edgar_artifacts
fi
```

### Multiple Environments

```bash
# Development
export EDGAR_ARTIFACTS_DIR=~/dev/edgar_artifacts

# Staging
export EDGAR_ARTIFACTS_DIR=/mnt/staging/edgar_artifacts

# Production
export EDGAR_ARTIFACTS_DIR=/var/edgar/artifacts
```

---

## Environment Variable Reference

### Variable Name
`EDGAR_ARTIFACTS_DIR`

### Expected Value
- Absolute or relative path to directory
- Tilde (`~`) expansion supported
- Spaces in path supported
- Must be writable

### Default Behavior
When not set, uses current working directory (project root)

### Scope
- Process-wide (affects all CLI commands in session)
- Inherited by child processes
- Not persisted between sessions (unless in shell profile)

### Platform Support
- ✅ macOS (tested)
- ✅ Linux (expected to work)
- ⏳ Windows (future support)

---

## See Also

- [Quick Start Guide](QUICK_START.md) - Getting started with EDGAR
- [CLI Usage Guide](CLI_USAGE.md) - Complete CLI reference
- [Project Structure](../architecture/PROJECT_STRUCTURE.md) - Codebase organization
- [Test Report](../../tests/EXTERNAL_ARTIFACTS_TEST_REPORT.md) - Full test results

---

## Support

### Questions?

1. Check configuration:
   ```bash
   python -c 'from edgar_analyzer.config.settings import get_artifacts_dir; print(get_artifacts_dir())'
   ```

2. Verify directory exists:
   ```bash
   ls -la $EDGAR_ARTIFACTS_DIR
   ```

3. Test with temporary directory:
   ```bash
   export EDGAR_ARTIFACTS_DIR=/tmp/test
   python -c 'from edgar_analyzer.config.settings import ensure_artifacts_structure; ensure_artifacts_structure()'
   ```

### Reporting Issues

Include in bug reports:
- Value of `$EDGAR_ARTIFACTS_DIR`
- Output of `get_artifacts_dir()`
- Directory permissions (`ls -ld $EDGAR_ARTIFACTS_DIR`)
- Error messages (full stack trace)

---

**Last Updated**: 2025-11-29
**Feature Version**: v0.1.0
**Status**: Production Ready ✅
