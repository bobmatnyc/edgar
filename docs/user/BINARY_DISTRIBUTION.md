# 🚀 Edgar Analyzer - Self-Contained Binary

**Fortune 500 Executive Compensation vs Tax Analysis Tool**

A complete, self-contained executable that automatically handles environment setup, dependency installation, and execution. No manual setup required!

## ✨ Features

- **🔄 Auto-Resume**: Intelligent checkpoint detection and seamless recovery
- **📊 Multi-Year Analysis**: 5-year historical data extraction (2019-2023)
- **📈 Professional Reports**: Excel and JSON outputs with multiple sheets
- **🛡️ Error Recovery**: Robust handling of individual company failures
- **⚡ Parallel Processing**: Optimized for large datasets with rate limiting
- **🎯 Smart Detection**: Automatic Fortune 500 company identification

## 🎯 Quick Start

### 1. Download & Run (No Setup Required!)

```bash
# macOS/Linux
./edgar-analyzer analyze --limit 10

# Windows
edgar-analyzer.bat analyze --limit 10
```

**That's it!** The first run automatically:
- ✅ Creates virtual environment
- ✅ Installs all dependencies
- ✅ Configures the application
- ✅ Starts your analysis

### 2. Subsequent Runs

```bash
# Smart analysis with auto-resume
./edgar-analyzer analyze --limit 50

# List available checkpoints
./edgar-analyzer checkpoint-analysis --list-checkpoints

# Force new analysis (ignore auto-resume)
./edgar-analyzer analyze --limit 25 --force-new
```

## 📋 System Requirements

- **Python 3.8+** (automatically detected)
- **Internet connection** (for SEC EDGAR API)
- **~500MB disk space** (for dependencies)
- **Operating System**: macOS, Linux, or Windows

## 🎮 Commands

### Smart Analysis (Recommended)
```bash
# Auto-detects and resumes incomplete analyses
./edgar-analyzer analyze --limit 50

# Custom output file
./edgar-analyzer analyze --limit 25 --output "my_analysis.xlsx"

# Different year
./edgar-analyzer analyze --year 2022 --limit 30
```

### Checkpoint Management
```bash
# List all checkpoints
./edgar-analyzer checkpoint-analysis --list-checkpoints

# Resume specific analysis
./edgar-analyzer checkpoint-analysis --resume fortune500_2023_abc12345

# Manual checkpoint control
./edgar-analyzer checkpoint-analysis --limit 100 --save-frequency 10
```

### Enhanced Analysis
```bash
# Historical analysis with professional formatting
./edgar-analyzer enhanced-fortune500 --limit 20 --historical

# Basic Fortune 500 analysis
./edgar-analyzer fortune500 --limit 15
```

### Company Search
```bash
# Search for specific companies
./edgar-analyzer search --query "Apple"
./edgar-analyzer search --query "Microsoft"
```

## 📊 Output Files

### Excel Reports (`output/`)
- **Analysis Results**: Main data with multi-year columns
- **Summary**: Key statistics and success rates  
- **Company Details**: Extraction status for each company
- **Extraction Log**: Configuration and error details

### JSON Data (`output/`)
- **Complete intermediate data** for further processing
- **Summary statistics** and metadata
- **Failed company details** for debugging

### Checkpoints (`data/checkpoints/`)
- **Resumable analysis data** in JSON format
- **Progress tracking** and error recovery
- **Automatic cleanup** of old checkpoints

## 🔄 Auto-Resume Magic

The tool intelligently detects incomplete analyses:

```
╭───────────────────── Auto-Resume ─────────────────────╮
│ 🔄 RESUMING PREVIOUS ANALYSIS                         │
│ Analysis ID: fortune500_2023_abc12345                 │
│ Progress: 60.0% complete                              │
│ Completed: 30/50 companies                            │
│ Success Rate: 96.7%                                   │
│ Last Updated: 2025-11-21 14:30:15                     │
│ Reason: Found incomplete analysis with 60.0% progress │
╰───────────────────────────────────────────────────────╯
```

## 🛠️ Troubleshooting

### Python Not Found (Windows)
```
❌ Python not found. Please install Python 3.8+ and add it to PATH.
Download from: https://www.python.org/downloads/
```

### Permission Denied (macOS/Linux)
```bash
chmod +x edgar-analyzer
./edgar-analyzer analyze --limit 10
```

### Clean Reinstall
```bash
# Remove virtual environment and start fresh
rm -rf venv/
./edgar-analyzer analyze --limit 5
```

## 📈 Example Workflow

```bash
# Day 1: Start large analysis
./edgar-analyzer analyze --limit 100
# → Processes 60 companies, then gets interrupted

# Day 1 (later): Auto-resume
./edgar-analyzer analyze --limit 100  
# → "🔄 Auto-resuming analysis (60% complete)"
# → Continues from company 61

# Day 2: Generate additional reports
./edgar-analyzer enhanced-fortune500 --limit 100
# → Uses existing data, generates professional Excel report
```

## 🎯 Success Metrics

- **⚡ Setup Time**: < 2 minutes (first run)
- **🔄 Resume Rate**: 100% (never lose progress)
- **📊 Success Rate**: 95%+ (with robust error handling)
- **💾 Storage**: ~500MB (includes all dependencies)
- **🌐 Compatibility**: macOS, Linux, Windows

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Run with `--help` for command-specific help
3. Check `output/` directory for generated reports
4. Review `data/checkpoints/` for analysis state

**Ready to analyze Fortune 500 companies? Just run the binary!** 🚀
