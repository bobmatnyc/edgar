@echo off
REM Edgar Analyzer - Self-Contained Fortune 500 Analysis Tool (Windows)
REM
REM This batch file automatically handles:
REM - Virtual environment setup
REM - Dependency installation  
REM - Application execution
REM
REM Usage:
REM     edgar-analyzer.bat analyze --limit 50
REM     edgar-analyzer.bat checkpoint-analysis --list-checkpoints
REM     edgar-analyzer.bat --help

setlocal enabledelayedexpansion

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+ and add it to PATH.
    echo Download from: https://www.python.org/downloads/
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% detected

REM Set paths
set "VENV_DIR=%SCRIPT_DIR%\venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "EDGAR_EXE=%VENV_DIR%\Scripts\edgar-analyzer.exe"

REM Check if setup is needed
if not exist "%VENV_DIR%" (
    set NEEDS_SETUP=1
) else if not exist "%EDGAR_EXE%" (
    set NEEDS_SETUP=1
) else (
    set NEEDS_SETUP=0
)

REM Show help if no arguments or help requested
if "%~1"=="" goto :show_help
if "%~1"=="--help" goto :show_help
if "%~1"=="-h" goto :show_help
if "%~1"=="help" goto :show_help

REM Setup environment if needed
if !NEEDS_SETUP!==1 (
    echo 🔧 First run detected - setting up environment...
    call :setup_environment
    if errorlevel 1 (
        echo ❌ Setup failed. Please check the error messages above.
        exit /b 1
    )
    echo.
)

REM Execute the command
if exist "%EDGAR_EXE%" (
    "%EDGAR_EXE%" %*
) else (
    "%PYTHON_EXE%" -m edgar_analyzer.cli.main %*
)
exit /b %errorlevel%

:setup_environment
echo 🚀 Edgar Analyzer - Self-Contained Setup
echo ==================================================

REM Create virtual environment
if not exist "%VENV_DIR%" (
    echo 🔧 Creating virtual environment: %VENV_DIR%
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        exit /b 1
    )
    echo ✅ Virtual environment created successfully
) else (
    echo ✅ Virtual environment already exists: %VENV_DIR%
)

REM Install dependencies
echo 🔧 Installing dependencies...
"%PYTHON_EXE%" -m pip install --upgrade pip >nul 2>&1
if errorlevel 1 (
    echo ❌ Failed to upgrade pip
    exit /b 1
)

"%PYTHON_EXE%" -m pip install -r "%SCRIPT_DIR%\requirements.txt" >nul 2>&1
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    exit /b 1
)
echo ✅ Dependencies installed successfully

REM Install package
echo 🔧 Installing edgar-analyzer package...
cd /d "%SCRIPT_DIR%"
"%PYTHON_EXE%" -m pip install -e . >nul 2>&1
if errorlevel 1 (
    echo ❌ Failed to install package
    exit /b 1
)
echo ✅ Edgar Analyzer package installed successfully

echo ==================================================
echo ✅ Edgar Analyzer setup complete!
echo 🎉 Ready to analyze Fortune 500 companies!
echo.
exit /b 0

:show_help
echo.
echo 🚀 Edgar Analyzer - Fortune 500 Analysis Tool
echo.
echo USAGE:
echo     edgar-analyzer.bat ^<command^> [options]
echo.
echo COMMANDS:
echo     analyze                     Smart analysis with auto-resume
echo     checkpoint-analysis         Manual checkpoint control
echo     enhanced-fortune500         Enhanced analysis with historical data
echo     fortune500                  Basic Fortune 500 analysis
echo     search                      Search for companies
echo.
echo EXAMPLES:
echo     # Smart analysis (recommended)
echo     edgar-analyzer.bat analyze --limit 50
echo.
echo     # Force new analysis
echo     edgar-analyzer.bat analyze --limit 25 --force-new
echo.
echo     # List checkpoints
echo     edgar-analyzer.bat checkpoint-analysis --list-checkpoints
echo.
echo     # Resume specific analysis
echo     edgar-analyzer.bat checkpoint-analysis --resume fortune500_2023_abc12345
echo.
echo     # Enhanced analysis with historical data
echo     edgar-analyzer.bat enhanced-fortune500 --limit 10 --historical
echo.
echo SETUP:
echo     The first run will automatically:
echo     ✅ Create virtual environment
echo     ✅ Install dependencies
echo     ✅ Configure the application
echo.
echo     Subsequent runs will use the existing environment.
echo.
echo REQUIREMENTS:
echo     - Python 3.8+
echo     - Internet connection (for SEC EDGAR API)
echo     - ~500MB disk space for dependencies
echo.
echo For detailed help on any command:
echo     edgar-analyzer.bat ^<command^> --help
echo.
exit /b 0
