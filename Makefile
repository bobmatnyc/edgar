# EDGAR Analyzer - Standardized Build Commands
# Single-path workflows for all common tasks

.PHONY: help install dev test lint format typecheck quality clean build deploy docs

# Default target - show help
help:
	@echo "EDGAR Analyzer - Available Commands"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make install          Install dependencies and setup environment"
	@echo "  make dev              Start development environment"
	@echo "  make test             Run all tests"
	@echo ""
	@echo "📊 Analysis:"
	@echo "  make extract          Extract data for a single company (requires CIK=xxx YEAR=xxx)"
	@echo "  make analyze-fortune  Analyze Fortune 500 companies"
	@echo "  make generate-reports Generate CSV and Excel reports"
	@echo ""
	@echo "🔍 Code Quality:"
	@echo "  make quality          Run all quality checks (lint, format, typecheck, test)"
	@echo "  make lint             Run code linting (flake8)"
	@echo "  make lint-fix         Auto-fix code formatting (black + isort)"
	@echo "  make format           Format code (black + isort)"
	@echo "  make typecheck        Run type checking (mypy)"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-coverage    Run tests with coverage report"
	@echo "  make test-xbrl        Test XBRL extraction"
	@echo ""
	@echo "📦 Build & Deploy:"
	@echo "  make build            Build deployment package"
	@echo "  make deploy           Create deployment package (alias for build)"
	@echo "  make package          Build Python package"
	@echo "  make clean            Clean build artifacts and cache"
	@echo ""
	@echo "📚 Documentation:"
	@echo "  make docs             Open documentation hub"
	@echo "  make docs-serve       Serve documentation locally"
	@echo ""
	@echo "🛠️  Development:"
	@echo "  make setup            Complete development setup"
	@echo "  make pre-commit       Install pre-commit hooks"
	@echo "  make venv             Create virtual environment"

# Installation and setup
install:
	@echo "📦 Installing dependencies..."
	pip install -e ".[dev]"
	@echo "✅ Installation complete!"

venv:
	@echo "🔧 Creating virtual environment..."
	python3 -m venv venv
	@echo "✅ Virtual environment created!"
	@echo "   Activate with: source venv/bin/activate"

setup: venv
	@echo "🚀 Setting up development environment..."
	. venv/bin/activate && pip install -e ".[dev]"
	. venv/bin/activate && pre-commit install
	cp -n .env.template .env.local || true
	@echo "✅ Development environment ready!"
	@echo "   1. Activate venv: source venv/bin/activate"
	@echo "   2. Edit .env.local with your API keys"
	@echo "   3. Run: make dev"

pre-commit:
	@echo "🔧 Installing pre-commit hooks..."
	pre-commit install
	@echo "✅ Pre-commit hooks installed!"

# Development
dev:
	@echo "🚀 Starting EDGAR Analyzer in development mode..."
	python -m edgar_analyzer

# Analysis commands
extract:
ifndef CIK
	@echo "❌ Error: CIK required"
	@echo "   Usage: make extract CIK=0000320193 YEAR=2023"
	@exit 1
endif
ifndef YEAR
	@echo "❌ Error: YEAR required"
	@echo "   Usage: make extract CIK=0000320193 YEAR=2023"
	@exit 1
endif
	@echo "📊 Extracting data for CIK $(CIK), Year $(YEAR)..."
	python -m edgar_analyzer extract --cik $(CIK) --year $(YEAR)

analyze-fortune:
	@echo "📊 Analyzing Fortune 500 companies..."
	python tests/run_complete_fortune_100_with_real_data.py

generate-reports:
	@echo "📊 Generating reports..."
	python create_csv_reports.py
	python create_report_spreadsheet.py
	@echo "✅ Reports generated in output/ directory"

# Code quality
quality: lint typecheck test
	@echo "✅ All quality checks passed!"

lint:
	@echo "🔍 Running code linting..."
	flake8 src/ tests/

lint-fix: format
	@echo "✅ Code auto-fixed!"

format:
	@echo "🎨 Formatting code..."
	black src/ tests/
	isort src/ tests/
	@echo "✅ Code formatted!"

typecheck:
	@echo "🔍 Running type checks..."
	mypy src/

# Testing
test:
	@echo "🧪 Running all tests..."
	pytest tests/

test-unit:
	@echo "🧪 Running unit tests..."
	pytest tests/unit/

test-integration:
	@echo "🧪 Running integration tests..."
	pytest tests/integration/

test-coverage:
	@echo "🧪 Running tests with coverage..."
	pytest --cov=src/edgar_analyzer --cov-report=term-missing --cov-report=html tests/
	@echo "📊 Coverage report generated: htmlcov/index.html"

test-xbrl:
	@echo "🧪 Testing XBRL extraction..."
	python tests/test_breakthrough_xbrl_service.py
	python tests/test_xbrl_executive_compensation.py

test-qa:
	@echo "🧪 Running comprehensive QA..."
	python tests/run_comprehensive_qa.py

# Build and deployment
build:
	@echo "📦 Building deployment package..."
	python create_deployment_package.py
	@echo "✅ Package created: edgar-analyzer-package.zip"

deploy: build
	@echo "✅ Deployment package ready!"

package:
	@echo "📦 Building Python package..."
	python -m build
	@echo "✅ Package built in dist/"

# Cleaning
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	@echo "✅ Cleanup complete!"

clean-cache:
	@echo "🧹 Cleaning data cache..."
	rm -rf data/cache/*
	@echo "✅ Cache cleaned!"

clean-all: clean clean-cache
	@echo "🧹 Deep cleaning..."
	rm -rf venv/
	rm -rf edgar-analyzer-package/
	rm -rf edgar-analyzer-package.zip
	@echo "✅ All cleaned!"

# Documentation
docs:
	@echo "📚 Opening documentation..."
	open docs/README.md || xdg-open docs/README.md || start docs/README.md

docs-serve:
	@echo "📚 Serving documentation..."
	python -m http.server 8000 --directory docs/

# Validation
validate-docs:
	@echo "🔍 Validating documentation links..."
	@find docs/ -name "*.md" -type f -exec grep -H "](.*\.md)" {} \; | while read line; do \
		echo "$$line"; \
	done

validate-structure:
	@echo "🔍 Validating project structure..."
	@test -f pyproject.toml || (echo "❌ pyproject.toml missing" && exit 1)
	@test -f CLAUDE.md || (echo "❌ CLAUDE.md missing" && exit 1)
	@test -d src/edgar_analyzer || (echo "❌ src/edgar_analyzer missing" && exit 1)
	@test -d tests || (echo "❌ tests directory missing" && exit 1)
	@test -d docs || (echo "❌ docs directory missing" && exit 1)
	@echo "✅ Project structure valid!"

# Version management
version:
	@echo "📋 Current version:"
	@grep "version =" pyproject.toml | head -1

# Quick actions
quick-test:
	@echo "⚡ Running quick tests (unit only)..."
	pytest tests/unit/ -v

quick-format:
	@echo "⚡ Quick format (changed files only)..."
	black src/ tests/ --quiet
	isort src/ tests/ --quiet
	@echo "✅ Done!"

# Development workflow
workflow: format lint typecheck test
	@echo "✅ Complete development workflow passed!"

# CI/CD simulation
ci: validate-structure quality test-coverage
	@echo "✅ CI pipeline simulation complete!"
