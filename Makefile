.PHONY: help install test lint format typecheck quality clean dev

help: ## Show this help message
	@echo "EDGAR Platform - Available Make Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies in virtual environment
	python3.11 -m venv venv
	. venv/bin/activate && pip install -e ".[dev]"
	@echo "✅ Dependencies installed. Activate venv with: source venv/bin/activate"

test: ## Run all tests
	pytest

test-unit: ## Run unit tests only
	pytest tests/unit/

test-integration: ## Run integration tests only
	pytest tests/integration/

test-coverage: ## Run tests with coverage report
	pytest --cov=edgar --cov-report=html
	@echo "📊 Coverage report generated in htmlcov/index.html"

lint: ## Check code with ruff
	ruff check src/

lint-fix: ## Auto-fix linting issues with ruff
	ruff check --fix src/

format: ## Format code with black
	black src/ tests/

format-check: ## Check formatting without changes
	black --check src/ tests/

typecheck: ## Run mypy type checking
	mypy src/

quality: ## Run all quality checks (typecheck + lint + format-check + test)
	@echo "🔍 Running type checking..."
	@mypy src/
	@echo "✅ Type checking passed"
	@echo ""
	@echo "🔍 Running linting..."
	@ruff check src/
	@echo "✅ Linting passed"
	@echo ""
	@echo "🔍 Checking formatting..."
	@black --check src/ tests/
	@echo "✅ Formatting check passed"
	@echo ""
	@echo "🧪 Running tests..."
	@pytest
	@echo "✅ All quality checks passed!"

clean: ## Clean build artifacts and cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage build/ dist/
	@echo "🧹 Cleaned build artifacts and cache"

dev: ## Quick dev setup (install + quality check)
	@$(MAKE) install
	@echo ""
	@echo "⚙️  Setting up development environment..."
	@echo ""
	@$(MAKE) quality
	@echo ""
	@echo "✅ Development environment ready!"
	@echo "📝 Don't forget to create .env file with OPENROUTER_API_KEY"
