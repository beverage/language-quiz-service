# LLM Observability

This document describes the observability features implemented for LLM API calls in the Language Quiz Service.

## Overview

The LLM clients (`src/clients/openai_client.py` and `src/clients/gemini_client.py`) include comprehensive observability instrumentation using OpenTelemetry to track performance, usage, and errors. Both clients support reasoning/thinking models and provide consistent metrics across providers.

## Metrics

Custom OpenTelemetry metrics are exported for all LLM requests:

### Request Metrics
- **`llm.request.duration`** (histogram, ms) - Duration of LLM API requests
  - Labels: `model`, `status`, `operation` (optional)
  
- **`llm.request.total`** (counter) - Total number of LLM API requests
  - Labels: `model`, `status`, `operation` (optional), `error_type` (on errors)

### Token Usage Metrics
- **`llm.tokens.input`** (counter) - Total input/prompt tokens consumed
  - Labels: `model`, `status`, `operation` (optional), `provider` (Gemini only)
  
- **`llm.tokens.output`** (counter) - Total output/completion tokens generated
  - Labels: `model`, `status`, `operation` (optional), `provider` (Gemini only)
  
- **`llm.tokens.reasoning`** (counter) - Total reasoning/thinking tokens consumed (gpt-5 models via OpenAI, or Gemini models with thinking enabled)
  - Labels: `model`, `status`, `operation` (optional), `provider` (Gemini only)
  
- **`llm.tokens.total`** (counter) - Total tokens (input + output)
  - Labels: `model`, `status`, `operation` (optional), `provider` (Gemini only)

## Span Attributes

All LLM calls add detailed attributes to the current OpenTelemetry trace span:

### Success Attributes
- `llm.model` - Model name (e.g., "gpt-4o-mini", "gemini-2.5-flash")
- `llm.operation` - Operation type (e.g., "verb_analysis", "sentence_generation")
- `llm.provider` - Provider name (Gemini only: "gemini")
- `llm.request.duration_ms` - Request duration in milliseconds
- `llm.response.id` - Response ID for correlation (OpenAI provides API response ID, Gemini generates timestamp-based ID)
- `llm.usage.prompt_tokens` - Number of input tokens
- `llm.usage.completion_tokens` - Number of output tokens
- `llm.usage.total_tokens` - Total tokens used
- `llm.usage.reasoning_tokens` - Number of reasoning tokens (OpenAI gpt-5 models only, if available)
- `llm.usage.thinking_tokens` - Number of thinking tokens (Gemini models only, if available)

### Error Attributes
- `llm.model` - Model name
- `llm.operation` - Operation type (if provided)
- `llm.request.duration_ms` - Request duration before failure
- `llm.error.type` - Exception type (e.g., "RateLimitError")
- `llm.error.message` - Error message

## Operation Labels

The following operation labels are used throughout the service:

| Operation | Purpose |
|-----------|---------|
| `verb_analysis` | Analyzing verb conjugations and patterns |
| `verb_object_detection` | Detecting direct/indirect objects in verb usage |
| `conjugation_generation` | Generating verb conjugations |
| `sentence_generation` | Generating new French sentences |
| `sentence_validation` | Validating correctness of generated sentences (if used) |

## Dashboard

The "LLM Performance" dashboard in Grafana provides real-time visualization of:
- Request rates and counts
- Latency percentiles (p50, p95, p99)
- Error rates and error types
- Token usage over time (shows actual token counts per 1-minute window using `increase()`, not rates)
- Token usage by operation
- Critical alerts (insufficient funds, error types)

The token usage panel shows actual token counts consumed in each time window, making it easy to see the exact token usage per LLM call rather than tokens per second.

## Dashboard Validation and Deployment

Dashboards are defined as code using `grafana-foundation-sdk` and can be validated and deployed to Grafana (local or cloud).

### Prerequisites

For local deployment:
```bash
# Start Grafana and Prometheus
docker-compose up -d grafana prometheus otel-collector
```

For cloud deployment, ensure you have:
- `GRAFANA_CLOUD_INSTANCE_ID` environment variable set
- `GRAFANA_CLOUD_API_KEY` environment variable set

### Validation

Validate dashboard definitions before deployment:
```bash
make dashboards-validate
```

This checks that all dashboard JSON is valid and can be parsed. Validation runs automatically in CI/CD pipelines when dashboard code changes.

### Deployment

Deploy dashboards to Grafana:
```bash
make dashboards-deploy
```

The deployment script automatically detects the environment:
- **Local**: Connects to `http://localhost:3000` (no auth required)
- **Cloud**: Uses `GRAFANA_CLOUD_INSTANCE_ID` and `GRAFANA_CLOUD_API_KEY` from environment

Dashboards are deployed to the "Language Quiz Service" folder in Grafana and will overwrite existing dashboards with the same UID.

### Export

Export dashboards as JSON files for inspection or backup:
```bash
make dashboards-export
```

This generates JSON files in `./dashboards/` directory for each dashboard.

### CI/CD Integration

Dashboard changes are automatically validated and deployed via GitHub Actions:
- **Validation**: Runs on all PRs that modify `src/observability/**`
- **Deployment**: Runs on pushes to `main` and `staging` branches
- See `.github/workflows/deploy-dashboards.yml` for details

## Provider-Specific Notes

### OpenAI
- Uses Chat Completions API for standard models (gpt-4o-mini)
- Uses Responses API for reasoning models (gpt-5) to capture reasoning summaries
- Metrics do not include a `provider` label
- Reasoning tokens are extracted from `usage.output_tokens_details.reasoning_tokens`

### Gemini
- Uses Google's genai SDK with `thinking_config` for thinking support
- Metrics include a `provider="gemini"` label for filtering
- Thinking tokens are extracted from `usage_metadata.thoughts_token_count`
- Span attributes use `llm.usage.thinking_tokens` (not `reasoning_tokens`)

## General Notes

- The `operation` parameter is optional but recommended for better observability
- Token metrics are only recorded when the API provides usage data in the response
- Reasoning/thinking tokens are only recorded when the value is greater than 0
- Span attributes are only set when a span is actively recording
- All metrics use the `environment` label for filtering by deployment stage (added by OpenTelemetry collector)
- Both clients use the unified metric name `llm.tokens.reasoning` for consistency, even though Gemini internally calls them "thinking tokens"

