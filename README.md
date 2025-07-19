<div align="center">

  [![Staging Deployment](https://github.com/beverage/language-quiz-service/actions/workflows/staging.yml/badge.svg)](https://github.com/beverage/language-quiz-service/actions/workflows/staging.yml)
  [![Production Deployment](https://github.com/beverage/language-quiz-service/actions/workflows/production.yml/badge.svg)](https://github.com/beverage/language-quiz-service/actions/workflows/production.yml)
  [![Coverage](https://codecov.io/gh/beverage/language-quiz-service/branch/staging/graph/badge.svg)](https://codecov.io/gh/beverage/language-quiz-service)
  [![Last Commit](https://img.shields.io/github/last-commit/beverage/language-quiz-service)](https://github.com/beverage/language-quiz-service/commits)
  [![License](https://img.shields.io/github/license/beverage/language-quiz-service)](LICENSE)

  [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
  [![Top Language](https://img.shields.io/github/languages/top/beverage/language-quiz-service?style=plastic)](https://github.com/beverage/language-quiz-service)
  [![](https://tokei.rs/b1/github/beverage/language-quiz-service?category=code)](https://github.com/XAMPPRocky/tokei)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.112+-green.svg)](https://fastapi.tiangolo.com)
  [![Pytest](https://img.shields.io/badge/Testing-pytest-orange?logo=pytest)](https://docs.pytest.org/)
  [![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

  [![Poetry](https://img.shields.io/badge/Poetry-dependency%20management-blue?logo=poetry)](https://python-poetry.org/)
  [![Supabase](https://img.shields.io/badge/Supabase-database-green?logo=supabase)](https://supabase.com/)
  [![Fly.io](https://img.shields.io/badge/Deployed%20on-Fly.io-purple?logo=fly.io)](https://fly.io/)
  [![OpenAI](https://img.shields.io/badge/OpenAI-API-black?logo=openai)](https://openai.com/)

  ![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/beverage/7990c61b7f48992ce2b2366d4422d8ab/raw/test.json)
  ![personal-website](https://img.shields.io/badge/Website-beverage.me-darkblue)
  [![Buymeacoffee](https://badgen.net/badge/icon/buymeacoffee?icon=buymeacoffee&label)](https://www.buymeacoffee.com/mrbeverage)
</div>

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
Required environment variables (create a `.env` file in the project root):
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

**Generate a random problem:**
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
├── api/                 # REST API endpoints
├── cli/                 # Command-line interface
├── core/                # Configuration and utilities
├── clients/             # External service clients
├── repositories/        # Data access layer
├── schemas/             # Pydantic models
├── services/            # Business logic layer
└── main.py              # FastAPI application entry point
```
