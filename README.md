<div align="center">

  [![Staging Deployment](https://github.com/beverage/language-quiz-service/actions/workflows/staging.yml/badge.svg)](https://github.com/beverage/language-quiz-service/actions/workflows/staging.yml)
  [![Production Deployment](https://github.com/beverage/language-quiz-service/actions/workflows/production.yml/badge.svg)](https://github.com/beverage/language-quiz-service/actions/workflows/production.yml)
  [![Last Commit](https://img.shields.io/github/last-commit/beverage/language-quiz-service)](https://github.com/beverage/language-quiz-service/commits)
  [![personal-website](https://img.shields.io/badge/Website-beverage.me-000000)](https://www.beverage.me)
  [![Buymeacoffee](https://badgen.net/badge/icon/buymeacoffee?icon=buymeacoffee&label)](https://www.buymeacoffee.com/mrbeverage)
</div>

| | |
|-|-|
| __Stack:__ | [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/) [![FastAPI](https://img.shields.io/badge/FastAPI-0.112+-green.svg)](https://fastapi.tiangolo.com) [![Supabase](https://img.shields.io/badge/Stored%20on-Supabase-3ecf8e?logo=supabase)](https://supabase.com/) [![Fly.io](https://img.shields.io/badge/Deployed%20on-Fly.io-7c3aed?logo=fly.io)](https://fly.io/) |
| __Tools:__ | [![OpenAI](https://img.shields.io/badge/OpenAI-10A37F?logo=openai)](https://openai.com/) [![Poetry](https://img.shields.io/badge/Depends%20on-Poetry-60a5fa?logo=poetry)](https://python-poetry.org/) [![Pytest](https://img.shields.io/badge/Tested%20with-pytest-orange?logo=pytest)](https://docs.pytest.org/) [![Code style: ruff](https://img.shields.io/badge/Styled%20by-ruff-000000?logo=ruff)](https://github.com/astral-sh/ruff) |
| __Stats:__ | [![Top Language](https://img.shields.io/github/languages/top/beverage/language-quiz-service?style=plastic)](https://github.com/beverage/language-quiz-service) [![Coverage](https://codecov.io/gh/beverage/language-quiz-service/branch/staging/graph/badge.svg)](https://codecov.io/gh/beverage/language-quiz-service) |


# Language Quiz Service

A FastAPI-powered backend service for generating AI-driven language learning quizzes and content. This service provides REST APIs for creating French language learning materials including verbs, sentences, and grammar problems.

Problem generation example:

![Example](docs/example.gif)

> A difficulty selector is still needed and on the todo list, as is the shortest sentence almost always being correct issue.
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

## 📋 Prerequisites

### Dependencies
Install via [Poetry](https://python-poetry.org/):
```bash
pipx install poetry
pipx inject poetry poetry-plugin-shell
poetry install
```

### Environment Variables
Required environment variables to operate the conolse app (create a `.env` file in the project root):
```bash
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_PROJECT_REF=your_supabase_project_ref

# Optional: Server Configuration
WEB_HOST=0.0.0.0
WEB_PORT=8000
```

## 🖥️ Command Line Interface

The CLI provides direct access to core functionality for development and testing with flexible output formatting:

**Initialize the database:**
```bash
lqs database init
```

**Generate some random problems:**
```bash
lqs problem random --count 5
```

**Get a random verb with different output formats:**
```bash
# Pretty format (default) - colorized tree view
lqs verb random

# Compact format - single line key=value pairs
lqs verb random --format compact

# Table format - structured table with types
lqs verb random --format table

# JSON format - raw JSON for scripting
lqs verb random --json
```

**Generate sentences:**
```bash
lqs sentence new --quantity 3
```

**Output Format Options:**
All CLI commands support consistent output formatting:
- `--format pretty` (default): Colorized tree view with emojis
- `--format compact`: Single-line key=value format
- `--format table`: Structured table with data types
- `--json`: Raw JSON output for scripting and automation

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
make test          # Run tests
make lint          # Run linting
make format        # Format code
make check         # Run format, lint, and test
```

### Testing
```bash
make test             # All tests
make test-unit        # Unit tests only
make test-integration # Integration tests only
```

See [tests/TESTING.md](./tests/TESTING.md) for test strategy and organization.

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

The service is layed out as follows:

```
src/
├── api/                 # REST API endpoints
├── cli/                 # Command-line interface
├── core/                # Configuration and utilities
├── clients/             # External service clients
├── repositories/        # Data access layer
├── schemas/             # Pydantic models
├── services/            # Business logic layer
└── main.py              # FastAPI application entry point
```
