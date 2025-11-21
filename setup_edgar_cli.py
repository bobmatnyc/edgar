#!/usr/bin/env python3
"""
EDGAR CLI Setup Binary

This script automatically sets up the complete EDGAR CLI environment:
- Creates virtual environment
- Installs all dependencies
- Configures environment variables
- Tests system components
- Provides ready-to-use CLI interface

Usage:
    python setup_edgar_cli.py
    
Or make it executable:
    chmod +x setup_edgar_cli.py
    ./setup_edgar_cli.py
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path

class EdgarCLISetup:
    """Automated setup for EDGAR CLI system."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        self.requirements = [
            "requests>=2.31.0",
            "beautifulsoup4>=4.12.0",
            "lxml>=4.9.0",
            "structlog>=23.1.0",
            "click>=8.1.0",
            "python-dotenv>=1.0.0",
            "aiohttp>=3.8.0",
            "asyncio-throttle>=1.0.0",
            "sqlalchemy>=2.0.0",
            "alembic>=1.11.0",
            "psycopg2-binary>=2.9.0",
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0"
        ]
        
    def print_header(self):
        """Print setup header."""
        print("🚀 EDGAR CLI Automated Setup")
        print("=" * 60)
        print("Setting up complete EDGAR analysis environment:")
        print("• Virtual environment creation")
        print("• Dependency installation")
        print("• Environment configuration")
        print("• System validation")
        print("• CLI interface preparation")
        print("=" * 60)
    
    def check_python_version(self):
        """Check Python version compatibility."""
        print("\n🐍 Checking Python version...")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print(f"❌ Python {version.major}.{version.minor} detected")
            print("   EDGAR CLI requires Python 3.8 or higher")
            print("   Please upgrade Python and try again")
            sys.exit(1)
        
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    
    def create_virtual_environment(self):
        """Create and activate virtual environment."""
        print("\n📦 Creating virtual environment...")
        
        if self.venv_path.exists():
            print("⚠️  Virtual environment already exists")
            response = input("   Remove and recreate? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                print("   Removing existing virtual environment...")
                shutil.rmtree(self.venv_path)
            else:
                print("   Using existing virtual environment")
                return
        
        try:
            subprocess.run([
                sys.executable, "-m", "venv", str(self.venv_path)
            ], check=True)
            print("✅ Virtual environment created successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            sys.exit(1)
    
    def get_venv_python(self):
        """Get path to virtual environment Python executable."""
        if os.name == 'nt':  # Windows
            return self.venv_path / "Scripts" / "python.exe"
        else:  # Unix/Linux/macOS
            return self.venv_path / "bin" / "python"
    
    def get_venv_pip(self):
        """Get path to virtual environment pip executable."""
        if os.name == 'nt':  # Windows
            return self.venv_path / "Scripts" / "pip.exe"
        else:  # Unix/Linux/macOS
            return self.venv_path / "bin" / "pip"
    
    def install_dependencies(self):
        """Install all required dependencies."""
        print("\n📚 Installing dependencies...")
        
        pip_path = self.get_venv_pip()
        
        # Upgrade pip first
        try:
            subprocess.run([
                str(pip_path), "install", "--upgrade", "pip"
            ], check=True)
            print("✅ pip upgraded successfully")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Could not upgrade pip: {e}")
        
        # Install requirements
        for requirement in self.requirements:
            try:
                print(f"   Installing {requirement}...")
                subprocess.run([
                    str(pip_path), "install", requirement
                ], check=True, capture_output=True)
                print(f"   ✅ {requirement}")
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Failed to install {requirement}: {e}")
                print("   Continuing with other packages...")
        
        print("✅ Dependencies installation complete")
    
    def create_environment_config(self):
        """Create environment configuration file."""
        print("\n⚙️  Creating environment configuration...")
        
        env_file = self.project_root / ".env"
        
        if env_file.exists():
            print("⚠️  .env file already exists")
            response = input("   Overwrite? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("   Keeping existing .env file")
                return
        
        env_content = """# EDGAR CLI Environment Configuration

# LLM Service Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
PRIMARY_MODEL=x-ai/grok-4.1-fast
FALLBACK_MODEL=anthropic/claude-3.5-sonnet

# EDGAR API Configuration
EDGAR_USER_AGENT=YourCompany YourEmail@example.com
EDGAR_API_BASE_URL=https://data.sec.gov

# Database Configuration (Optional)
DATABASE_URL=postgresql://user:password@localhost/edgar_db

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# CLI Configuration
CLI_MODE=auto  # auto, chatbot, traditional
SCRIPTING_ENABLED=true
MAX_EXECUTION_TIME=30.0

# Performance Configuration
MAX_CONCURRENT_REQUESTS=5
REQUEST_DELAY=0.1
CACHE_ENABLED=true
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("✅ Environment configuration created")
        print(f"   📝 Edit {env_file} to configure your API keys")
    
    def create_launcher_scripts(self):
        """Create convenient launcher scripts."""
        print("\n🚀 Creating launcher scripts...")
        
        # Unix/Linux/macOS launcher
        launcher_sh = self.project_root / "edgar_cli.sh"
        launcher_content_sh = f"""#!/bin/bash
# EDGAR CLI Launcher Script

cd "{self.project_root}"
source venv/bin/activate
python -m edgar_analyzer.cli "$@"
"""
        
        with open(launcher_sh, 'w') as f:
            f.write(launcher_content_sh)
        
        # Make executable
        os.chmod(launcher_sh, 0o755)
        
        # Windows launcher
        launcher_bat = self.project_root / "edgar_cli.bat"
        launcher_content_bat = f"""@echo off
REM EDGAR CLI Launcher Script

cd /d "{self.project_root}"
call venv\\Scripts\\activate.bat
python -m edgar_analyzer.cli %*
"""
        
        with open(launcher_bat, 'w') as f:
            f.write(launcher_content_bat)
        
        print("✅ Launcher scripts created")
        print(f"   🐧 Unix/Linux/macOS: ./edgar_cli.sh")
        print(f"   🪟 Windows: edgar_cli.bat")
    
    def test_installation(self):
        """Test the installation."""
        print("\n🧪 Testing installation...")
        
        python_path = self.get_venv_python()
        
        # Test basic imports
        test_script = """
import sys
sys.path.insert(0, 'src')

try:
    from edgar_analyzer.services.edgar_service import EdgarService
    print("✅ EDGAR service import successful")
except Exception as e:
    print(f"❌ EDGAR service import failed: {e}")

try:
    from cli_chatbot import ChatbotController
    print("✅ CLI Chatbot import successful")
except Exception as e:
    print(f"❌ CLI Chatbot import failed: {e}")

try:
    from self_improving_code import SelfImprovingController
    print("✅ Self-improving code import successful")
except Exception as e:
    print(f"❌ Self-improving code import failed: {e}")

print("🎉 Installation test complete")
"""
        
        try:
            result = subprocess.run([
                str(python_path), "-c", test_script
            ], capture_output=True, text=True, cwd=self.project_root)
            
            print(result.stdout)
            if result.stderr:
                print("Warnings/Errors:")
                print(result.stderr)
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Installation test failed: {e}")
    
    def print_completion_message(self):
        """Print completion message with usage instructions."""
        print("\n" + "=" * 60)
        print("🎉 EDGAR CLI SETUP COMPLETE!")
        print("=" * 60)
        
        print("\n🚀 **READY TO USE:**")
        print("   Your EDGAR CLI environment is fully configured")
        
        print("\n📋 **NEXT STEPS:**")
        print("   1. Edit .env file with your API keys")
        print("   2. Run test: python test_50_companies.py")
        print("   3. Start CLI: ./edgar_cli.sh (or edgar_cli.bat on Windows)")
        
        print("\n💬 **CLI MODES:**")
        print("   • Conversational: Natural language interface with LLM")
        print("   • Traditional: Structured CLI commands (fallback)")
        print("   • Automatic: Detects LLM availability and chooses mode")
        
        print("\n🛠️  **EXAMPLE USAGE:**")
        print("   ./edgar_cli.sh                    # Start interactive mode")
        print("   ./edgar_cli.sh analyze --help     # Show analysis options")
        print("   ./edgar_cli.sh execute --help     # Show execution options")
        
        print("\n📚 **DOCUMENTATION:**")
        print("   • README.md - General documentation")
        print("   • src/cli_chatbot/README.md - CLI documentation")
        print("   • src/self_improving_code/README.md - Pattern documentation")
        
        print("\n🎯 **SYSTEM FEATURES:**")
        print("   ✅ Self-improving code with LLM QA")
        print("   ✅ Conversational CLI interface")
        print("   ✅ Subprocess monitoring and safety")
        print("   ✅ Automatic fallback mechanisms")
        print("   ✅ Real-time context injection")
        print("   ✅ Professional-grade safety and validation")
    
    def run_setup(self):
        """Run the complete setup process."""
        self.print_header()
        self.check_python_version()
        self.create_virtual_environment()
        self.install_dependencies()
        self.create_environment_config()
        self.create_launcher_scripts()
        self.test_installation()
        self.print_completion_message()

if __name__ == "__main__":
    setup = EdgarCLISetup()
    setup.run_setup()
