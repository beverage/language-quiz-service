<div align="center">

  [![Staging Deployment](https://github.com/beverage/language-quiz-service/actions/workflows/staging.yml/badge.svg)](https://github.com/beverage/language-quiz-service/actions/workflows/staging.yml)
  [![Production Deployment](https://github.com/beverage/language-quiz-service/actions/workflows/production.yml/badge.svg)](https://github.com/beverage/language-quiz-service/actions/workflows/production.yml)
  [![Last Commit](https://img.shields.io/github/last-commit/beverage/language-quiz-service)](https://github.com/beverage/language-quiz-service/commits)
  [![personal-website](https://img.shields.io/badge/Website-beverage.me-000000)](https://www.beverage.me)
  [![Buymeacoffee](https://badgen.net/badge/icon/buymeacoffee?icon=buymeacoffee&label)](https://www.buymeacoffee.com/mrbeverage)
</div>

| | |
|-|-|
| __Stack:__ | [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/) [![FastAPI](https://img.shields.io/badge/FastAPI-0.112+-green.svg)](https://fastapi.tiangolo.com) [![Supabase](https://img.shields.io/badge/Stored%20on-Supabase-3ecf8e?logo=supabase)](https://supabase.com/) [![Fly.io](https://img.shields.io/badge/Deployed%20on-Fly.io-7c3aed?logo=fly.io)](https://fly.io/) [![OpenAI](https://img.shields.io/badge/OpenAI-10A37F?logo=openai)](https://openai.com/) [![Gemini](https://img.shields.io/badge/Gemini-8E75B2?logo=googlegemini)](https://ai.google.dev/) [![Kafka](https://img.shields.io/badge/Kafka-231F20?logo=apachekafka)](https://kafka.apache.org/) |
| __Tools:__ | [![Poetry](https://img.shields.io/badge/Depends%20on-Poetry-60a5fa?logo=poetry)](https://python-poetry.org/) [![Pytest](https://img.shields.io/badge/Tested%20with-pytest-orange?logo=pytest)](https://docs.pytest.org/) [![Code style: ruff](https://img.shields.io/badge/Styled%20by-ruff-000000?logo=ruff)](https://github.com/astral-sh/ruff) |
| __Stats:__ | [![Top Language](https://img.shields.io/github/languages/top/beverage/language-quiz-service?style=plastic)](https://github.com/beverage/language-quiz-service) [![Coverage](https://codecov.io/gh/beverage/language-quiz-service/branch/staging/graph/badge.svg)](https://codecov.io/gh/beverage/language-quiz-service) |


# Language Quiz Service

A FastAPI backend service for generating AI-powered French grammar quiz problems. Uses compositional prompts and multiple LLM providers to create pedagogically-focused learning content with targeted grammatical errors.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- [Supabase CLI](https://supabase.com/docs/guides/cli) (for local development)
- LLM API key (OpenAI and/or Gemini)

### Environment Variables

Create a `.env` file in the project root:

```bash
# LLM Provider (required - at least one)
OPENAI_API_KEY=your_openai_api_key      # Required if using OpenAI
GEMINI_API_KEY=your_gemini_api_key      # Required if using Gemini
LLM_PROVIDER=gemini                      # Options: openai, gemini

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### Start the Service

```bash
# 1. Start local Supabase (required - runs separately)
make start-supabase

# 2. Start the development stack
docker-compose up
```

This starts the following services:

| Service | Port | Description |
|---------|------|-------------|
| **FastAPI App** | 8000 | API server with embedded Kafka workers |
| **Kafka** | 9092 | Message queue for async problem generation |
| **OpenTelemetry Collector** | 4317/4318 | Receives traces and metrics |
| **Prometheus** | 9090 | Metrics storage |
| **Grafana** | 3000 | Dashboards (user: `lqs`, pass: `test`) |

The service will be available at:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Grafana Dashboards**: http://localhost:3000

## Features

- **Async problem generation** via Kafka workers with status tracking
- **Multi-provider LLM support** for OpenAI and Google Gemini
- **107 French verbs** with complete conjugation tables across major tenses
- **Compositional prompt system** generating targeted grammatical errors
- **REST API** with OpenAPI documentation and API key authentication
- **Full observability** with OpenTelemetry, Prometheus, and Grafana

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System design, data flow, and key decisions |
| [Development Guide](docs/development.md) | Development workflows and CLI reference |
| [Operations Playbook](docs/operations-playbook.md) | Common operations using `lqs` CLI |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/problems/grammar/random` | GET | Get a random grammar problem from the pool (LRU) with optional filters |
| `/api/v1/problems/{id}` | GET | Get a specific problem by ID |
| `/api/v1/problems/generate` | POST | Trigger async problem generation |
| `/api/v1/generation-requests/{id}` | GET | Check generation request status |
| `/api/v1/verbs/{infinitive}` | GET | Get verb details by infinitive |
| `/api/v1/cache/stats` | GET | View cache statistics |

Full API documentation available at `/docs` when running the service, or view the [hosted API reference](https://registry.scalar.com/@lqs/apis/language-quiz-service-api/latest).

## CLI Quick Reference

The `lqs` CLI provides direct access to core functionality:

```bash
# Initialize the database with verbs
lqs database init

# Generate problems asynchronously
lqs problem generate -c 5

# Check generation status
lqs generation status <request-id>

# Get a random grammar problem
lqs problem random grammar

# Get a random grammar problem with filters
lqs problem random grammar --focus conjugation --tenses futur_simple

# View problem with LLM reasoning trace
lqs problem get <uuid> --llm-trace
```

See [Operations Playbook](docs/operations-playbook.md) for comprehensive CLI usage.

## Project Structure

```
src/
├── api/           # REST API endpoints
├── cli/           # Command-line interface (lqs)
├── clients/       # LLM clients (OpenAI, Gemini)
├── prompts/       # Compositional prompt system
├── services/      # Business logic
├── worker/        # Kafka consumers
└── main.py        # Application entry
```

## License

MIT License - see [LICENSE](LICENSE)