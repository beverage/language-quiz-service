.PHONY: help lint lint-check lint-fix lint-fix-unsafe format test serve dev dev-monitored build deploy logs up down start-supabase setup dashboards-deploy dashboards-validate dashboards-export

# Default target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Development:"
	@echo "  setup           - First-time local environment setup"
	@echo "  dev             - Start FastAPI development server (fast, no monitoring)"
	@echo "  dev-monitored   - Start with Grafana Cloud observability"
	@echo "  serve           - Start FastAPI server (production mode)"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint-check      - Check code with ruff"
	@echo "  lint-fix        - Fix linting issues with ruff"
	@echo "  lint-fix-unsafe - Fix linting issues with ruff (including unsafe fixes)"
	@echo "  lint            - Run both lint-check and lint-fix"
	@echo "  format          - Format code with ruff"
	@echo ""
	@echo "Testing:"
	@echo "  test            - Run all tests"
	@echo "  start-supabase  - Start Supabase with minimal containers for testing"
	@echo ""
	@echo "Observability:"
	@echo "  dashboards-deploy   - Deploy dashboards to Grafana (local or cloud)"
	@echo "  dashboards-validate - Validate dashboard definitions"
	@echo "  dashboards-export   - Export dashboards as JSON files"
	@echo ""
	@echo "Deployment:"
	@echo "  build           - Build Docker container"
	@echo "  deploy          - Deploy to fly.io (ENV=staging|production, default: staging)"
	@echo "  logs            - Show service logs (ENV=staging|production, default: staging)"
	@echo "  up              - Start all machines (ENV=staging|production, default: staging)"
	@echo "  down            - Stop all machines (ENV=staging|production, default: staging)"
	@echo ""
	@echo "Examples:"
	@echo "  make setup                 # First-time setup"
	@echo "  make dev                   # Fast local development"
	@echo "  make dev-monitored         # Local development with observability"
	@echo "  make dashboards-deploy     # Deploy dashboards"
	@echo "  make deploy ENV=staging    # Deploy to staging"
	@echo "  make deploy ENV=production # Deploy to production"

# Setup targets
setup:
	@echo "Setting up local development environment..."
	@./scripts/setup-local-env.sh

# FastAPI development targets
serve:
	@echo "Starting FastAPI server..."
	poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000

dev:
	@echo "Starting FastAPI development server (fast, no monitoring)..."
	poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

dev-monitored:
	@echo "Starting FastAPI with Grafana Cloud observability..."
	@./scripts/dev-with-monitoring.sh


# Docker targets
build:
	@echo "Building Docker container..."
	docker build -t language-quiz-service .

# Environment configuration (default: staging)
ENV ?= staging

# Deployment targets
deploy:
	@echo "Deploying to $(ENV) environment..."
	flyctl deploy --app language-quiz-app-$(ENV) --remote-only --flycast

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

# Observability targets
.PHONY: dashboards-deploy dashboards-validate dashboards-export
dashboards-deploy:
	@echo "Deploying dashboards to Grafana..."
	poetry run python -m src.observability.deploy

dashboards-validate:
	@echo "Validating dashboard definitions..."
	poetry run python -m src.observability.deploy --validate

dashboards-export:
	@echo "Exporting dashboards as JSON..."
	poetry run python -m src.observability.deploy --export --output-dir ./dashboards 