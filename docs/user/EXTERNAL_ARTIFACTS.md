# Using External Artifacts Directory

Store all EDGAR platform outputs outside the repository for cleaner version control and unlimited storage.

## Overview

The EDGAR platform supports an external artifacts directory via the `EDGAR_ARTIFACTS_DIR` environment variable. This allows you to:

- ✅ Keep your repository clean (no large data files in git)
- ✅ Use unlimited external storage (separate disk/drive)
- ✅ Easily backup all project artifacts (single directory)
- ✅ Share artifacts across multiple repository clones
- ✅ Separate dev/prod environments cleanly

## Quick Start

### 1. Set Environment Variable

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, or `~/.profile`):

```bash
export EDGAR_ARTIFACTS_DIR=~/edgar_projects
```

Or set for current session only:

```bash
export EDGAR_ARTIFACTS_DIR=~/edgar_projects
```

### 2. Restart Terminal or Source Profile

```bash
source ~/.bashrc  # or ~/.zshrc
```

### 3. Verify Configuration

```bash
echo $EDGAR_ARTIFACTS_DIR
# Expected output: /Users/yourname/edgar_projects
```

### 4. Run Commands (Directory Created Automatically)

```bash
# Create a project - goes to external directory
edgar-analyzer project create my-api --template weather

# Project created at: ~/edgar_projects/projects/my-api/
```

## Directory Structure

When `EDGAR_ARTIFACTS_DIR` is set, the platform creates this structure:

```
$EDGAR_ARTIFACTS_DIR/
├── output/                  # Global reports (Excel, JSON, CSV)
│   ├── enhanced_fortune500_analysis_2023.xlsx
│   ├── checkpoint_analysis_2023.xlsx
│   └── quality_test_2023.xlsx
├── projects/                # User-created project workspaces
│   ├── weather_api/
│   │   ├── project.yaml
│   │   ├── examples/
│   │   ├── src/
│   │   ├── tests/
│   │   └── output/          # Per-project outputs
│   ├── employee_roster/
│   └── invoice_transform/
├── data/                    # Platform data directories
│   ├── cache/               # API response cache
│   ├── checkpoints/         # Analysis checkpoints
│   └── backups/             # Database backups
└── logs/                    # Log files
    └── edgar_analyzer.log
```

## Configuration Behavior

### Without Environment Variable

If `EDGAR_ARTIFACTS_DIR` is **not set**, the platform uses in-repo directories:

```
edgar/  (repository root)
├── output/           # Reports here
├── projects/         # Projects here
├── data/
│   ├── cache/
│   ├── checkpoints/
│   └── backups/
└── logs/
```

### With Environment Variable

If `EDGAR_ARTIFACTS_DIR` **is set**, all artifacts go to external directory:

```bash
export EDGAR_ARTIFACTS_DIR=~/edgar_projects

# Projects created in: ~/edgar_projects/projects/
# Reports saved to: ~/edgar_projects/output/
# Cache stored in: ~/edgar_projects/data/cache/
```

### Override with CLI Flag

You can still override the directory for specific commands:

```bash
# Use custom directory for this command only
edgar-analyzer project create test --output-dir /tmp/test_projects
```

## Examples

### Example 1: Basic Setup

```bash
# Set environment variable
export EDGAR_ARTIFACTS_DIR=~/edgar_projects

# Create project
edgar-analyzer project create weather-data --template weather

# List projects (shows projects in external directory)
edgar-analyzer project list

# Output:
# Projects (1)
# ┌─────────────┬─────────┬──────────┬─────────────────────┐
# │ Name        │ Version │ Template │ Description         │
# ├─────────────┼─────────┼──────────┼─────────────────────┤
# │ weather-data│ 0.1.0   │ weather  │                     │
# └─────────────┴─────────┴──────────┴─────────────────────┘
```

### Example 2: Multiple Environments

```bash
# Development environment
export EDGAR_ARTIFACTS_DIR=~/edgar_dev
edgar-analyzer project create dev-api --template minimal

# Production environment (separate terminal/session)
export EDGAR_ARTIFACTS_DIR=~/edgar_prod
edgar-analyzer project create prod-api --template minimal

# Each environment has isolated projects and outputs
```

### Example 3: Shared Storage

```bash
# Use external drive for large projects
export EDGAR_ARTIFACTS_DIR=/Volumes/ExternalDrive/edgar_projects
edgar-analyzer project create large-dataset --template minimal

# All artifacts stored on external drive (unlimited space)
```

## Migration Guide

### Moving Existing Projects to External Directory

If you already have projects in the repository, here's how to move them:

```bash
# 1. Set environment variable
export EDGAR_ARTIFACTS_DIR=~/edgar_projects

# 2. Create external directory structure
mkdir -p ~/edgar_projects

# 3. Move existing projects (optional)
mv projects ~/edgar_projects/
mv output ~/edgar_projects/

# 4. Move data directories (optional)
mv data ~/edgar_projects/

# 5. Verify
edgar-analyzer project list
# Should show all your projects from external directory
```

## Environment Variable Details

### Valid Values

- **Absolute paths**: `/Users/yourname/edgar_projects`
- **Relative to home**: `~/edgar_projects` (expands to home directory)
- **Relative paths**: `./artifacts` (resolved from current directory)
- **Empty string**: Treated as unset (uses in-repo defaults)

### Error Handling

**Directory doesn't exist**:
```
Creating external artifacts directory: ~/edgar_projects
```
(Directory created automatically with warning)

**Permission denied**:
```
Error: Cannot create artifacts directory at ~/edgar_projects: Permission denied
```
(Command fails with helpful error message)

**Points to file (not directory)**:
```
Error: EDGAR_ARTIFACTS_DIR must be a directory, not a file: ~/file.txt
```
(Command fails with validation error)

## Troubleshooting

### Problem: "Where are my files?"

**Solution**: Check if `EDGAR_ARTIFACTS_DIR` is set:

```bash
echo $EDGAR_ARTIFACTS_DIR
```

If set, your files are in the external directory. If not set, they're in the repository.

### Problem: Files not found after moving repository

**Solution**: Update `EDGAR_ARTIFACTS_DIR` to new location:

```bash
# Old: export EDGAR_ARTIFACTS_DIR=/old/path/edgar_projects
# New:
export EDGAR_ARTIFACTS_DIR=/new/path/edgar_projects
```

### Problem: Permission errors

**Solution**: Check directory permissions:

```bash
ls -ld $EDGAR_ARTIFACTS_DIR
# Should show: drwxr-xr-x (user has write permission)

# Fix permissions if needed:
chmod u+w $EDGAR_ARTIFACTS_DIR
```

### Problem: Want to use in-repo defaults again

**Solution**: Unset the environment variable:

```bash
unset EDGAR_ARTIFACTS_DIR
```

## Benefits

### Clean Repository

- No large data files in git
- Faster `git status` and `git add`
- Smaller repository size
- Easier to review pull requests

### Unlimited Storage

- Use external drives for large datasets
- No repository bloat concerns
- Scale to terabytes if needed

### Easy Backup

- Single directory to backup
- Simple backup scripts
- Cloud sync-friendly (Dropbox, Google Drive)

### Shared Access

- Multiple repository clones use same artifacts
- Team collaboration on shared drive
- Environment-specific separation

## Advanced Configuration

### Per-Session Override

```bash
# Temporary override (doesn't change shell profile)
EDGAR_ARTIFACTS_DIR=/tmp/test_run edgar-analyzer project create test-proj
```

### Docker/Container Usage

```dockerfile
# Dockerfile
ENV EDGAR_ARTIFACTS_DIR=/app/artifacts
VOLUME /app/artifacts
```

### CI/CD Integration

```yaml
# GitHub Actions
env:
  EDGAR_ARTIFACTS_DIR: ${{ github.workspace }}/artifacts

steps:
  - name: Create artifacts directory
    run: mkdir -p $EDGAR_ARTIFACTS_DIR

  - name: Run analysis
    run: edgar-analyzer extract --cik 0000320193 --year 2023

  - name: Upload artifacts
    uses: actions/upload-artifact@v3
    with:
      name: edgar-reports
      path: ${{ env.EDGAR_ARTIFACTS_DIR }}/output/
```

## Related Documentation

- [Quick Start Guide](QUICK_START.md) - Getting started with EDGAR platform
- [Excel File Transform](EXCEL_FILE_TRANSFORM.md) - Excel → JSON transformation
- [PDF File Transform](PDF_FILE_TRANSFORM.md) - PDF → JSON transformation
- [Project Management](../architecture/PROJECT_STRUCTURE.md) - Project organization

## Support

For issues or questions:

1. Check this guide's Troubleshooting section
2. Verify environment variable with `echo $EDGAR_ARTIFACTS_DIR`
3. Review error messages (they include suggested fixes)
4. See [CLAUDE.md](../../CLAUDE.md) for project overview

---

**Implementation Status**: ✅ Complete (Phase 2 - Core Platform Architecture)

**Last Updated**: 2025-11-29
