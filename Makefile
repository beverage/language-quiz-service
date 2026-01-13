.PHONY: help lint lint-check lint-fix lint-fix-unsafe format test serve dev dev-monitored build deploy logs up down start-supabase setup dashboards-deploy dashboards-validate dashboards-export kafka-deploy kafka-logs kafka-status kafka-ssh redis-deploy redis-logs redis-status redis-health redis-password redis-memory redis-security redis-restart redis-ssh redis-clean

# Default target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Development:"
	@echo "  setup           - First-time local environment setup"
	@echo "  compose-env     - Generate .env.compose.local from local Supabase"
	@echo "  compose-up      - Start docker-compose with local Supabase (recommended)"
	@echo "  dev             - Start FastAPI development server with local Supabase"
	@echo "  dev-monitored   - Start with Grafana Cloud observability"
	@echo "  serve           - Start FastAPI server (production mode)"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint-check      - Check code with ruff"
	@echo "  lint-fix        - Fix linting issues with ruff"
	@echo "  lint-fix-unsafe - Fix linting issues with ruff (including unsafe fixes)"
	@echo "  lint            - Run both lint-check and lint-fix"
	@echo "  format          - Format code with ruff"
	@echo "  format-check    - Check code formatting without modifying files"
	@echo ""
	@echo "Testing:"
	@echo "  test            - Run all tests"
	@echo "  test-unit       - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-acceptance - Run acceptance tests (local :7900 or remote if CI=true)"
	@echo "  test-cov        - Run tests with coverage report"
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
	@echo "Kafka (Infrastructure):"
	@echo "  kafka-deploy    - Deploy Kafka (ENV=staging|production, default: staging)"
	@echo "  kafka-logs      - Show Kafka logs (ENV=staging|production, default: staging)"
	@echo "  kafka-status    - Show Kafka status (ENV=staging|production, default: staging)"
	@echo "  kafka-ssh       - SSH into Kafka instance (ENV=staging|production, default: staging)"
	@echo ""
	@echo "Redis (Infrastructure):"
	@echo "  redis-deploy    - Deploy Redis (ENV=staging|production, default: staging)"
	@echo "  redis-logs      - Show Redis logs (ENV=staging|production, default: staging)"
	@echo "  redis-status    - Show Redis status (ENV=staging|production, default: staging)"
	@echo "  redis-health    - Check Redis health (ENV=staging|production, default: staging)"
	@echo "  redis-password  - Set Redis password (ENV=staging|production, default: staging)"
	@echo "  redis-memory    - Show Redis memory usage (ENV=staging|production, default: staging)"
	@echo "  redis-security  - Verify Redis is not publicly accessible"
	@echo "  redis-restart   - Restart Redis (ENV=staging|production, default: staging)"
	@echo "  redis-ssh       - SSH into Redis instance (ENV=staging|production, default: staging)"
	@echo ""
	@echo "Examples:"
	@echo "  make setup                 # First-time setup"
	@echo "  make compose-up            # Start with docker-compose (recommended)"
	@echo "  make dev                   # Fast local development (uvicorn)"
	@echo "  make dev-monitored         # Local development with observability"
	@echo "  make dashboards-deploy     # Deploy dashboards"
	@echo "  make deploy ENV=staging    # Deploy to staging"
	@echo "  make deploy ENV=production # Deploy to production"
	@echo "  make kafka-deploy ENV=staging  # Deploy Kafka to staging"
	@echo "  make redis-deploy ENV=staging  # Deploy Redis to staging"

# Setup targets
setup:
	@echo "Setting up local development environment..."
	@./scripts/setup-local-env.sh

# FastAPI development targets
serve:
	@echo "Starting FastAPI server..."
	poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000

compose-env:
	@echo "🔧 Generating .env.compose.local from local Supabase..."
	./scripts/generate_compose_env.sh

compose-up: compose-env
	@echo "🚀 Starting docker-compose with local Supabase..."
	docker-compose up --build

dev:
	@echo "🚀 Starting FastAPI development server with local Supabase..."
	@if ! supabase status >/dev/null 2>&1; then \
		echo "❌ Local Supabase is not running. Start it with: supabase start"; \
		exit 1; \
	fi
	@./scripts/generate_compose_env.sh >/dev/null
	@echo "✅ Using local Supabase configuration"
	@set -a && source .env.compose.local && set +a && \
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

format-check:
	@echo "Checking code formatting with ruff..."
	poetry run ruff format --check .

# Testing target
test:
	@echo "Running all tests (excluding acceptance)..."
	poetry run pytest -n auto -m "not acceptance"

# Testing with coverage
test-cov:
	@echo "Running all tests with coverage (excluding acceptance)..."
	poetry run pytest -n auto -m "not acceptance" --cov=src --cov-report=xml --cov-report=term-missing

.PHONY: test-unit
test-unit:
	@echo "Running unit tests..."
	poetry run pytest -n auto -m unit

.PHONY: test-integration
test-integration:
	@echo "Running integration tests..."
	poetry run pytest -n auto-m integration

.PHONY: test-acceptance kill-port-7900 _acceptance-stack-up _acceptance-stack-down
kill-port-7900:
	@echo "🔪 Killing any existing process on port 7900..."
	@lsof -ti:7900 | xargs kill -9 2>/dev/null || true
	@sleep 2
	@if lsof -ti:7900 >/dev/null 2>&1; then \
		echo "⚠️  Port 7900 still in use after kill attempt"; \
		lsof -i:7900; \
		exit 1; \
	else \
		echo "✅ Port 7900 is now free"; \
	fi

_acceptance-stack-up:
	@echo "🔧 Starting acceptance test service on :7900..."
	@if ! supabase status >/dev/null 2>&1; then \
		echo "❌ Local Supabase is not running. Start it with: supabase start"; \
		exit 1; \
	fi
	@echo "Starting development server in background..."
	@set -a; source .env; set +a; \
	REQUIRE_AUTH=true \
	SUPABASE_URL=http://127.0.0.1:54321 \
	SUPABASE_SERVICE_ROLE_KEY=$(shell supabase status --output json | jq -r '.SERVICE_ROLE_KEY') \
	poetry run uvicorn src.main:app --host 0.0.0.0 --port 7900 & echo $$! > .server_pid
	@echo "Server PID: $$(cat .server_pid)"
	@sleep 8
	@echo "✅ Service started on :7900"

_acceptance-stack-down:
	@echo "🛑 Stopping acceptance test service..."
	@SERVER_PID=$$(cat .server_pid 2>/dev/null || true); if [ -n "$$SERVER_PID" ]; then kill $$SERVER_PID 2>/dev/null || true; rm -f .server_pid; fi
	@sleep 2

test-acceptance:
	@echo "🎯 Running acceptance tests..."
	@# Load .env if it exists (for local development)
	@if [ -f .env ]; then \
		export $$(grep -v '^#' .env | grep SERVICE_API_KEY | xargs); \
	fi; \
	if [ "$$CI" = "true" ] || [ -n "$$SERVICE_URL" ]; then \
		echo "Testing against remote service: $$SERVICE_URL"; \
		if [ -z "$$SERVICE_API_KEY" ]; then \
			echo "❌ SERVICE_API_KEY is required for remote testing"; \
			exit 1; \
		fi; \
		mkdir -p artifacts/acceptance; \
		SERVICE_URL=$$SERVICE_URL SERVICE_API_KEY=$$SERVICE_API_KEY poetry run pytest --no-cov -m "acceptance" tests/acceptance --junitxml artifacts/acceptance/results.xml -v; \
	else \
		echo "Testing against local development server on :7900..."; \
		if [ -z "$$SERVICE_API_KEY" ]; then \
			echo "❌ SERVICE_API_KEY environment variable is required for local acceptance tests"; \
			echo "💡 Add SERVICE_API_KEY to your .env file"; \
			exit 1; \
		fi; \
		$(MAKE) kill-port-7900; \
		$(MAKE) _acceptance-stack-up; \
		echo "Running acceptance tests..."; \
		mkdir -p artifacts/acceptance; \
		SERVICE_URL=http://localhost:7900 SERVICE_API_KEY=$$SERVICE_API_KEY poetry run pytest --no-cov -m "acceptance" tests/acceptance --junitxml artifacts/acceptance/results.xml -v; \
		TEST_RESULT=$$?; \
		$(MAKE) _acceptance-stack-down; \
		if [ $$TEST_RESULT -eq 0 ]; then \
			echo "✅ Acceptance tests passed!"; \
		else \
			echo "❌ Acceptance tests failed!"; \
			exit 1; \
		fi; \
	fi

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

# Kafka deployment targets (manual, intentional)
kafka-deploy:
	@echo "Deploying Kafka to $(ENV) environment..."
	@if [ "$(ENV)" = "production" ]; then \
		echo "⚠️  WARNING: Deploying Kafka to PRODUCTION"; \
		echo "This will affect all production services."; \
		read -p "Are you sure? (yes/no): " confirm; \
		if [ "$$confirm" != "yes" ]; then \
			echo "Deployment cancelled."; \
			exit 1; \
		fi; \
	fi
	flyctl deploy --config infra/kafka/fly.$(ENV).toml \
		--app language-quiz-kafka-$(ENV) --ha=false

kafka-logs:
	@echo "Showing Kafka $(ENV) logs..."
	flyctl logs --app language-quiz-kafka-$(ENV)

kafka-status:
	@echo "Checking Kafka $(ENV) status..."
	flyctl status --app language-quiz-kafka-$(ENV)

kafka-ssh:
	@echo "SSH into Kafka $(ENV) instance..."
	flyctl ssh console --app language-quiz-kafka-$(ENV)

# Redis deployment targets (for rate limiting)
redis-deploy:
	@echo "Deploying Redis to $(ENV) environment..."
	@if [ "$(ENV)" = "production" ]; then \
		echo "⚠️  WARNING: Deploying Redis to PRODUCTION"; \
		read -p "Are you sure? (yes/no): " confirm; \
		if [ "$$confirm" != "yes" ]; then \
			echo "Deployment cancelled."; \
			exit 1; \
		fi; \
	fi
	@echo "1️⃣ Deploying application with flycast networking..."
	cd infra/redis/$(ENV) && flyctl deploy --flycast -c fly.toml
	@echo "✅ Redis deployment complete!"
	@echo "📝 Remember to set the Redis password with: make redis-password ENV=$(ENV)"

redis-logs:
	@echo "Showing Redis $(ENV) logs..."
	flyctl logs -c infra/redis/$(ENV)/fly.toml

redis-status:
	@echo "Checking Redis $(ENV) status..."
	flyctl status -c infra/redis/$(ENV)/fly.toml

redis-health:
	@echo "🏥 Redis Health Check ($(ENV))..."
	flyctl ssh console -c infra/redis/$(ENV)/fly.toml --command "redis-cli -a \$$REDIS_PASSWORD --no-auth-warning PING" && echo "✅ Redis is healthy!"

redis-password:
	@echo "🔐 Setting new Redis password for $(ENV)..."
	@NEW_PASSWORD=$$(openssl rand -base64 32); \
	flyctl secrets set REDIS_PASSWORD="$$NEW_PASSWORD" -c infra/redis/$(ENV)/fly.toml; \
	echo "✅ Password set! Save this password:"; \
	echo "$$NEW_PASSWORD"; \
	echo ""; \
	echo "Add to your application's secrets:"; \
	echo "  flyctl secrets set REDIS_HOST=lqs-redis-$(ENV).flycast \\"; \
	echo "                     REDIS_PORT=6379 \\"; \
	echo "                     REDIS_PASSWORD='$$NEW_PASSWORD' \\"; \
	echo "                     -a language-quiz-app-$(ENV)"

redis-memory:
	@echo "💾 Redis Memory Usage ($(ENV))..."
	flyctl ssh console -c infra/redis/$(ENV)/fly.toml --command "redis-cli -a \$$REDIS_PASSWORD --no-auth-warning INFO memory"

redis-security:
	@echo "🔒 Verifying Redis is not publicly accessible..."
	@bash infra/redis/verify-redis-security.sh

redis-restart:
	@echo "🔄 Restarting Redis ($(ENV))..."
	flyctl apps restart lqs-redis-$(ENV)

redis-ssh:
	@echo "SSH into Redis $(ENV) instance..."
	flyctl ssh console -c infra/redis/$(ENV)/fly.toml

redis-clean:
	@if [ "$(ENV)" = "production" ]; then \
		echo "❌ Cannot clean production Redis (FLUSHALL is disabled)"; \
		exit 1; \
	fi
	@echo "🧹 Clearing all data in $(ENV) Redis..."
	@read -p "⚠️  This will delete all data. Continue? (y/N): " confirm; \
	if [ "$$confirm" = "y" ]; then \
		flyctl ssh console -c infra/redis/$(ENV)/fly.toml --command "redis-cli -a \$$REDIS_PASSWORD --no-auth-warning FLUSHALL"; \
		echo "✅ Redis cleared!"; \
	else \
		echo "Cancelled."; \
	fi