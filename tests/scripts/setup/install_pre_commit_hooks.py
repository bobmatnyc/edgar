#!/usr/bin/env python3
"""
Script Name: install_pre_commit_hooks.py

PURPOSE:
    Install Git pre-commit hooks to enforce code governance standards.
    Ensures all commits meet quality requirements before being accepted.

FUNCTION:
    Pre-commit hook installation and configuration:
    - Creates Git pre-commit hook script
    - Configures automatic code standards validation
    - Sets up quality gates for file size, documentation, patterns
    - Enables automatic rejection of non-compliant commits

USAGE:
    python scripts/setup/install_pre_commit_hooks.py [options]
    
    Arguments:
        --force: Overwrite existing pre-commit hooks
        --dry-run: Show what would be installed without making changes
        --uninstall: Remove pre-commit hooks
    
    Examples:
        python scripts/setup/install_pre_commit_hooks.py
        python scripts/setup/install_pre_commit_hooks.py --force
        python scripts/setup/install_pre_commit_hooks.py --uninstall

MODIFICATION HISTORY:
    2025-11-21 System - Initial creation
    - WHY: Need automated enforcement at commit time
    - HOW: Git hooks with Python validation scripts
    - IMPACT: Prevents non-compliant code from entering repository

DEPENDENCIES:
    - Python 3.8+
    - Git repository
    - scripts/quality/enforce_code_standards.py

AUTHOR: EDGAR CLI System
CREATED: 2025-11-21
LAST_MODIFIED: 2025-11-21
"""

import sys
import os
import stat
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import structlog

logger = structlog.get_logger(__name__)


class PreCommitHookInstaller:
    """
    Installs and manages Git pre-commit hooks for code governance.
    
    WHY: Enforces code standards at commit time to prevent violations
    HOW: Creates Git hooks that run validation scripts before commits
    WHEN: Created 2025-11-21 for automated quality enforcement
    """
    
    def __init__(self, project_root: Path):
        """Initialize the pre-commit hook installer."""
        self.project_root = project_root
        self.git_hooks_dir = project_root / ".git" / "hooks"
        self.pre_commit_hook = self.git_hooks_dir / "pre-commit"
        
    def install_hooks(self, force: bool = False) -> bool:
        """
        Install pre-commit hooks for code governance.
        
        WHY: Automated quality enforcement at commit time
        HOW: Creates executable Git hook script with validation logic
        
        Args:
            force: Overwrite existing hooks if they exist
            
        Returns:
            True if installation successful, False otherwise
        """
        try:
            # Check if Git repository exists
            if not self.git_hooks_dir.exists():
                logger.error("Git repository not found", hooks_dir=str(self.git_hooks_dir))
                return False
            
            # Check if hook already exists
            if self.pre_commit_hook.exists() and not force:
                logger.warning("Pre-commit hook already exists", 
                             hook_path=str(self.pre_commit_hook))
                print("❌ Pre-commit hook already exists. Use --force to overwrite.")
                return False
            
            # Create hook script
            hook_content = self._create_hook_script()
            
            # Write hook file
            with open(self.pre_commit_hook, 'w') as f:
                f.write(hook_content)
            
            # Make executable
            self.pre_commit_hook.chmod(self.pre_commit_hook.stat().st_mode | stat.S_IEXEC)
            
            logger.info("Pre-commit hook installed successfully", 
                       hook_path=str(self.pre_commit_hook))
            print("✅ Pre-commit hook installed successfully!")
            print(f"   Hook location: {self.pre_commit_hook}")
            print("   Code governance will be enforced on all commits.")
            
            return True
            
        except Exception as e:
            logger.error("Failed to install pre-commit hook", error=str(e))
            print(f"❌ Failed to install pre-commit hook: {e}")
            return False
    
    def uninstall_hooks(self) -> bool:
        """
        Remove pre-commit hooks.
        
        WHY: Allow removal of hooks when needed
        HOW: Deletes the pre-commit hook file
        
        Returns:
            True if uninstallation successful, False otherwise
        """
        try:
            if self.pre_commit_hook.exists():
                self.pre_commit_hook.unlink()
                logger.info("Pre-commit hook removed", hook_path=str(self.pre_commit_hook))
                print("✅ Pre-commit hook removed successfully!")
                return True
            else:
                print("ℹ️  No pre-commit hook found to remove.")
                return True
                
        except Exception as e:
            logger.error("Failed to remove pre-commit hook", error=str(e))
            print(f"❌ Failed to remove pre-commit hook: {e}")
            return False
    
    def _create_hook_script(self) -> str:
        """
        Create the pre-commit hook script content.
        
        WHY: Need executable script that validates code before commits
        HOW: Creates shell script that runs Python validation
        
        Returns:
            Hook script content as string
        """
        return f"""#!/bin/bash
#
# EDGAR CLI Pre-Commit Hook
# Enforces code governance standards before allowing commits
#
# This hook runs automatically before each commit to validate:
# - File size limits (500 lines max for core code)
# - Documentation requirements (WHY/HOW/WHEN)
# - Service pattern compliance
# - Script organization standards
#

echo "🔍 Running EDGAR CLI code governance checks..."

# Get the project root directory
PROJECT_ROOT="{self.project_root}"

# Run code standards enforcement
python3 "$PROJECT_ROOT/scripts/quality/enforce_code_standards.py" --check-all

# Check the exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Code governance violations detected!"
    echo "   Please fix the violations above before committing."
    echo "   See CODE_GOVERNANCE.md for detailed standards."
    echo ""
    echo "💡 Quick fixes:"
    echo "   • Split large files (>500 lines) into smaller modules"
    echo "   • Add WHY/HOW/WHEN documentation to classes"
    echo "   • Follow service pattern for business logic"
    echo "   • Add proper script headers for utility scripts"
    echo ""
    exit 1
fi

echo "✅ All code governance standards met!"
echo "   Proceeding with commit..."
echo ""

# Allow the commit to proceed
exit 0
"""
    
    def check_hook_status(self) -> Dict[str, Any]:
        """
        Check the status of pre-commit hooks.
        
        WHY: Provide visibility into hook installation status
        HOW: Checks for hook file existence and permissions
        
        Returns:
            Dictionary with hook status information
        """
        status = {
            "installed": False,
            "executable": False,
            "path": str(self.pre_commit_hook),
            "git_repo_exists": self.git_hooks_dir.exists()
        }
        
        if self.pre_commit_hook.exists():
            status["installed"] = True
            
            # Check if executable
            file_stat = self.pre_commit_hook.stat()
            status["executable"] = bool(file_stat.st_mode & stat.S_IEXEC)
        
        return status


def main():
    """
    Main script execution function.
    
    WHY: Centralized entry point for pre-commit hook management
    HOW: Orchestrates installation, uninstallation, and status checking
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Install EDGAR CLI pre-commit hooks")
    parser.add_argument("--force", action="store_true", 
                       help="Overwrite existing pre-commit hooks")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be installed without making changes")
    parser.add_argument("--uninstall", action="store_true",
                       help="Remove pre-commit hooks")
    parser.add_argument("--status", action="store_true",
                       help="Check pre-commit hook status")
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    
    # Initialize installer
    installer = PreCommitHookInstaller(project_root)
    
    try:
        if args.status:
            # Check status
            status = installer.check_hook_status()
            print("📊 Pre-commit Hook Status:")
            print(f"   Git Repository: {'✅' if status['git_repo_exists'] else '❌'}")
            print(f"   Hook Installed: {'✅' if status['installed'] else '❌'}")
            print(f"   Hook Executable: {'✅' if status['executable'] else '❌'}")
            print(f"   Hook Path: {status['path']}")
            
        elif args.uninstall:
            # Uninstall hooks
            success = installer.uninstall_hooks()
            sys.exit(0 if success else 1)
            
        elif args.dry_run:
            # Show what would be installed
            print("🔍 Dry run - would install pre-commit hook:")
            print(f"   Hook location: {installer.pre_commit_hook}")
            print("   Hook would enforce:")
            print("   • File size limits (500 lines max)")
            print("   • Documentation requirements (WHY/HOW/WHEN)")
            print("   • Service pattern compliance")
            print("   • Script organization standards")
            
        else:
            # Install hooks
            success = installer.install_hooks(force=args.force)
            
            if success:
                print("\n🎯 Code governance is now enforced!")
                print("   All commits will be validated for:")
                print("   • Architectural compliance")
                print("   • Documentation standards")
                print("   • File size limits")
                print("   • Service patterns")
                print("\n📚 See CODE_GOVERNANCE.md for detailed standards.")
            
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Installation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected error", error=str(e))
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
