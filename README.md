[![Staging Deployment](https://github.com/beverage/language-quiz-service/actions/workflows/staging.yml/badge.svg)](https://github.com/beverage/language-quiz-service/actions/workflows/staging.yml)
[![Production Deployment](https://github.com/beverage/language-quiz-service/actions/workflows/production.yml/badge.svg)](https://github.com/beverage/language-quiz-service/actions/workflows/production.yml)
[![Coverage](https://codecov.io/gh/beverage/language-quiz-service/branch/staging/graph/badge.svg)](https://codecov.io/gh/beverage/language-quiz-service)
[![linting: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.112+-green.svg)](https://fastapi.tiangolo.com)
[![Buymeacoffee](https://badgen.net/badge/icon/buymeacoffee?icon=buymeacoffee&label)](https://www.buymeacoffee.com/mrbeverage)

![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/<user>/<gist-ID>/raw/test.json)

# Language Quiz Service

A FastAPI-powered backend service for generating AI-driven language learning quizzes and content. This service provides REST APIs for creating French language learning materials including verbs, sentences, and grammar problems.

![Example](docs/example.gif)
> This example is highly rate-limited and with randomised features.  Also, as of a few weeks ago looks nothing like this anymore, and is much more accurate.  I'll have to make a new one.

## 🚀 Quick Start

### FastAPI Service (Recommended)

Start the FastAPI development server:
```bash
make dev
```

Or manually with uvicorn:
```bash
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

The service will be available at:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Alternative Docs**: http://localhost:8000/redoc

### Docker Deployment

```bash
make build
docker run -p 8000:8000 language-quiz-service
```

## 📋 Prerequisites

### Dependencies
Install via [Poetry](https://python-poetry.org/):
```bash
pipx install poetry
pipx inject poetry poetry-plugin-shell
poetry install
```

### Environment Variables
Required environment variables:
```bash
# OpenAI API Key
export OPENAI_API_KEY=your_openai_api_key

# Supabase Configuration
export SUPABASE_URL=your_supabase_url
export SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key
export SUPABASE_ANON_KEY=your_supabase_anon_key
export SUPABASE_PROJECT_REF=your_supabase_project_ref

# Optional: Server Configuration
export WEB_HOST=0.0.0.0
export WEB_PORT=8000
```

### Database Setup
A PostgreSQL database is required. Use the provided docker-compose configuration:
```bash
docker-compose up
```

Initialize the database with essential verbs:
```bash
poetry run python -m src.cli database init
```

## 🖥️ Command Line Interface

The CLI provides direct access to core functionality for development and testing:

**Initialize the database:**
```bash
poetry run python -m src.cli database init
```

**Generate a random problem:**
```bash
poetry run python -m src.cli problem random --count 5
```

**Get a random verb:**
```bash
poetry run python -m src.cli verb random
```

**Generate sentences:**
```bash
poetry run python -m src.cli sentence new --quantity 3
```

**Legacy webserver commands:**
```bash
# These are now no-ops - use 'make dev' instead
poetry run python -m src.cli webserver start
```

## 🔧 Development

### Code Quality
Install pre-commit hooks:
```bash
make install-githooks
```

### Available Make Commands
```bash
make help          # Show all available commands
make dev           # Start FastAPI with auto-reload
make serve         # Start FastAPI server
make build         # Build Docker container
make test          # Run tests
make lint          # Run linting
make format        # Format code
make all           # Run format, lint, and test
```

### Testing
```bash
make test           # All tests
make test-unit      # Unit tests only
make test-integration # Integration tests only
```

## 📡 API Endpoints

### Health & Status
- `GET /` - Service information
- `GET /health` - Health check

### Core Resources
- `GET /api/v1/problems/random` - Generate random grammar problem
- `GET /api/v1/sentences/random` - Generate random sentence
- `GET /api/v1/verbs/random` - Get random verb

*Full API documentation available at `/docs` when running the service.*

## 🏗️ Architecture

The service follows a clean architecture pattern:

```
src/
├── main.py              # FastAPI application entry point
├── api/                 # REST API endpoints
├── services/            # Business logic layer
├── repositories/        # Data access layer
├── schemas/             # Pydantic models
├── core/                # Configuration and utilities
├── clients/             # External service clients
└── cli/                 # Command-line interface (legacy)
```

## 🚀 Deployment

### Production
```bash
# Build and run with Docker
make build
docker run -p 8000:8000 --env-file .env language-quiz-service
```

### Environment Configuration
- **Development**: Auto-reload enabled, debug logging
- **Production**: Optimized for performance, structured logging

## 📈 Roadmap

- [ ] REST API endpoints for all CLI functionality
- [ ] Authentication and authorization
- [ ] Rate limiting and caching
- [ ] Metrics and monitoring
- [ ] Multi-language support expansion
- [ ] Advanced grammar rule validation
