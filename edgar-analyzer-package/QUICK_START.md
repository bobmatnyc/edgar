# 🚀 Edgar Analyzer - Quick Start

## Installation & First Run

### macOS/Linux:
```bash
chmod +x edgar-analyzer
./edgar-analyzer analyze --limit 10
```

### Windows:
```cmd
edgar-analyzer.bat analyze --limit 10
```

## What Happens on First Run:
1. ✅ Checks Python 3.8+ availability
2. ✅ Creates virtual environment
3. ✅ Installs all dependencies
4. ✅ Configures the application
5. ✅ Starts your analysis

## Common Commands:
```bash
# Smart analysis with auto-resume
./edgar-analyzer analyze --limit 50

# List checkpoints
./edgar-analyzer checkpoint-analysis --list-checkpoints

# Enhanced analysis
./edgar-analyzer enhanced-fortune500 --limit 20

# Get help
./edgar-analyzer --help
```

## Output:
- **Excel reports**: `output/*.xlsx`
- **JSON data**: `output/*.json`
- **Checkpoints**: `data/checkpoints/*.json`

## Requirements:
- Python 3.8+
- Internet connection
- ~500MB disk space

**That's it! No manual setup required.** 🎉
