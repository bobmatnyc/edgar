#!/usr/bin/env python3
"""
Create deployment package for Edgar Analyzer.

This script creates a complete, self-contained deployment package
that can be distributed and run on any system with Python 3.8+.
"""

import os
import shutil
import zipfile
from pathlib import Path


def create_deployment_package():
    """Create complete deployment package."""
    
    print("🚀 Creating Edgar Analyzer Deployment Package")
    print("=" * 50)
    
    # Define paths
    source_dir = Path(__file__).parent
    package_dir = source_dir / "edgar-analyzer-package"
    
    # Clean up existing package directory
    if package_dir.exists():
        print(f"🧹 Cleaning up existing package: {package_dir}")
        shutil.rmtree(package_dir)
    
    # Create package directory
    print(f"📁 Creating package directory: {package_dir}")
    package_dir.mkdir()
    
    # Files and directories to include
    include_items = [
        # Core application
        "src/",
        "pyproject.toml",
        "requirements.txt",
        
        # Self-contained executables
        "edgar-analyzer",
        "edgar-analyzer.bat",
        
        # Documentation
        "README.md",
        "README_BINARY.md",
        
        # Sample data (if exists)
        "data/companies/fortune_500_complete.json",
        
        # Example configurations
        "docs/",
    ]
    
    # Copy files and directories
    for item in include_items:
        source_path = source_dir / item
        dest_path = package_dir / item
        
        if source_path.exists():
            if source_path.is_file():
                print(f"📄 Copying file: {item}")
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dest_path)
            elif source_path.is_dir():
                print(f"📁 Copying directory: {item}")
                shutil.copytree(source_path, dest_path, ignore=shutil.ignore_patterns(
                    '__pycache__', '*.pyc', '*.pyo', '.git', '.pytest_cache', 'venv', '.venv'
                ))
        else:
            print(f"⚠️  Skipping missing item: {item}")
    
    # Create output and data directories
    (package_dir / "output").mkdir(exist_ok=True)
    (package_dir / "data" / "checkpoints").mkdir(parents=True, exist_ok=True)
    
    # Create .gitignore for the package
    gitignore_content = """
# Virtual environment
venv/
.venv/

# Output files
output/*.xlsx
output/*.json

# Checkpoints
data/checkpoints/*.json

# Python cache
__pycache__/
*.pyc
*.pyo

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db
"""
    
    with open(package_dir / ".gitignore", "w") as f:
        f.write(gitignore_content.strip())
    
    # Create quick start guide
    quick_start = """# 🚀 Edgar Analyzer - Quick Start

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
"""
    
    with open(package_dir / "QUICK_START.md", "w") as f:
        f.write(quick_start)
    
    # Make executables executable (Unix systems)
    if os.name != 'nt':  # Not Windows
        os.chmod(package_dir / "edgar-analyzer", 0o755)
    
    print("✅ Package created successfully!")
    print(f"📦 Package location: {package_dir}")
    print()
    print("📋 Package contents:")
    for item in sorted(package_dir.rglob("*")):
        if item.is_file():
            relative_path = item.relative_to(package_dir)
            print(f"   📄 {relative_path}")
    
    # Create ZIP archive
    zip_path = source_dir / "edgar-analyzer-package.zip"
    print(f"\n📦 Creating ZIP archive: {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in package_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(package_dir.parent)
                zipf.write(file_path, arcname)
    
    print("✅ ZIP archive created successfully!")
    print()
    print("🎯 Deployment Instructions:")
    print("1. Distribute the ZIP file or package directory")
    print("2. Users extract and run:")
    print("   - macOS/Linux: ./edgar-analyzer analyze --limit 10")
    print("   - Windows: edgar-analyzer.bat analyze --limit 10")
    print("3. First run automatically sets up everything!")
    print()
    print("🎉 Ready for deployment!")


if __name__ == "__main__":
    create_deployment_package()
