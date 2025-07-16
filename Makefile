.PHONY: help lint lint-check lint-fix lint-fix-unsafe format test serve dev build deploy logs up down start-supabase

# Default target
help:
	@echo "Available targets:"
	@echo "  lint-check      - Check code with ruff"
	@echo "  lint-fix        - Fix linting issues with ruff"
	@echo "  lint-fix-unsafe - Fix linting issues with ruff (including unsafe fixes)"
	@echo "  lint            - Run both lint-check and lint-fix"
	@echo "  format          - Format code with ruff (excludes src/cli)"
	@echo "  test            - Run tests with pytest"
	@echo "  serve           - Start FastAPI development server"
	@echo "  dev             - Start FastAPI development server with auto-reload"
	@echo "  build           - Build Docker container"
	@echo "  deploy          - Deploy to fly.io (ENV=staging|production, default: staging)"
	@echo "  logs            - Show service logs (ENV=staging|production, default: staging)"
	@echo "  up              - Start all machines (ENV=staging|production, default: staging)"
	@echo "  down            - Stop all machines (ENV=staging|production, default: staging)"
	@echo "  start-supabase  - Start Supabase with minimal containers for testing"
	@echo "  all             - Run format, lint, and test"
	@echo ""
	@echo "Examples:"
	@echo "  make deploy ENV=staging    # Deploy to staging (default)"
	@echo "  make deploy ENV=production # Deploy to production"
	@echo "  make up     ENV=production # Start staging machines (default)"
	@echo "  make logs   ENV=production # Show production logs"

# FastAPI development targets
serve:
	@echo "Starting FastAPI server..."
	poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000

dev:
	@echo "Starting FastAPI development server with auto-reload..."
	poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Docker targets
build:
	@echo "Building Docker container..."
	docker build -t language-quiz-service .

# Environment configuration (default: staging)
ENV ?= staging

# Deployment targets
deploy:
	@echo "Deploying to $(ENV) environment..."
	flyctl deploy --config fly.$(ENV).toml --remote-only --flycast

# Fly.io management targets
logs:
	@echo "Showing $(ENV) logs..."
	flyctl logs --config fly.$(ENV).toml

up:
	@echo "Starting $(ENV) machines..."
	flyctl machine list --json --config fly.$(ENV).toml | jq -r '.[].id' | xargs -I {} flyctl machine start {} --config fly.$(ENV).toml

down:
	@echo "Stopping $(ENV) machines..."
	flyctl machine list --json --config fly.$(ENV).toml | jq -r '.[].id' | xargs -I {} flyctl machine stop {} --config fly.$(ENV).toml

# Supabase targets
start-supabase:
	@echo "Starting Supabase with minimal containers for testing..."
	supabase start -x realtime,storage-api,imgproxy,mailpit,postgres-meta,studio,edge-runtime,logflare,vector,supavisor

# Linting targets
lint-check:
	@echo "Running ruff check..."
	poetry run ruff check .

lint-fix:
	@echo "Fixing linting issues with ruff..."
	poetry run ruff check --fix .

lint-fix-unsafe:
	@echo "Fixing linting issues with ruff (including unsafe fixes)..."
	poetry run ruff check --fix --unsafe-fixes .

lint: lint-fix-unsafe lint-check

# Formatting target (exclude src/cli as requested)
format:
	@echo "Formatting code with ruff on the whole project..."
	poetry run ruff format .

# Testing target
test:
	@echo "Running all tests..."
	poetry run pytest -n auto

# Testing with coverage
test-cov:
	@echo "Running all tests with coverage..."
	poetry run pytest -n auto --cov=src --cov-report=xml --cov-report=term-missing

.PHONY: test-unit
test-unit:
	@echo "Running unit tests..."
	poetry run pytest -n auto-m unit

.PHONY: test-integration
test-integration:
	@echo "Running integration tests..."
	poetry run pytest -n auto-m integration

# Run everything
all: format lint test

# Git hooks installation
.PHONY: install-githooks
install-githooks:
	@echo "Installing git hooks..."
	@./scripts/install-githooks.sh 