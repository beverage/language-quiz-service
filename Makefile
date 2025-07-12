.PHONY: help lint lint-check lint-fix lint-fix-unsafe format test

# Default target
help:
	@echo "Available targets:"
	@echo "  lint-check    - Check code with ruff and pylint"
	@echo "  lint-fix      - Fix linting issues with ruff"
	@echo "  lint-fix-unsafe - Fix linting issues with ruff (including unsafe fixes)"
	@echo "  lint          - Run both lint-check and lint-fix"
	@echo "  format        - Format code with ruff (excludes src/cli)"
	@echo "  test          - Run tests with pytest"
	@echo "  all           - Run format, lint, and test"

# Linting targets
lint-check:
	@echo "Running ruff check..."
	poetry run ruff check .
	@echo "Running pylint..."
	poetry run pylint src/

lint-fix:
	@echo "Fixing linting issues with ruff..."
	poetry run ruff check --fix .

lint-fix-unsafe:
	@echo "Fixing linting issues with ruff (including unsafe fixes)..."
	poetry run ruff check --fix --unsafe-fixes .

lint: lint-fix lint-check

# Formatting target (exclude src/cli as requested)
format:
	@echo "Formatting code with ruff on the whole project..."
	poetry run ruff format .

# Testing target
test:
	@echo "Running all tests..."
	poetry run pytest

.PHONY: test-unit
test-unit:
	@echo "Running unit tests..."
	poetry run pytest -m unit

.PHONY: test-integration
test-integration:
	@echo "Running integration tests..."
	poetry run pytest -m integration

# Run everything
all: format lint test

# Git hooks installation
.PHONY: install-githooks
install-githooks:
	@echo "Installing git hooks..."
	@./scripts/install-githooks.sh 