# LLM Observability

This document describes the observability features implemented for LLM API calls in the Language Quiz Service.

## Overview

The OpenAI client (`src/clients/openai_client.py`) includes comprehensive observability instrumentation using OpenTelemetry to track performance, usage, and errors.

## Metrics

Custom OpenTelemetry metrics are exported for all LLM requests:

### Request Metrics
- **`llm.request.duration`** (histogram, ms) - Duration of LLM API requests
  - Labels: `model`, `status`, `operation` (optional)
  
- **`llm.request.total`** (counter) - Total number of LLM API requests
  - Labels: `model`, `status`, `operation` (optional), `error_type` (on errors)

### Token Usage Metrics
- **`llm.tokens.input`** (counter) - Total input/prompt tokens consumed
  - Labels: `model`, `status`, `operation` (optional)
  
- **`llm.tokens.output`** (counter) - Total output/completion tokens generated
  - Labels: `model`, `status`, `operation` (optional)
  
- **`llm.tokens.total`** (counter) - Total tokens (input + output)
  - Labels: `model`, `status`, `operation` (optional)

## Span Attributes

All LLM calls add detailed attributes to the current OpenTelemetry trace span:

### Success Attributes
- `llm.model` - Model name (e.g., "gpt-4o-mini")
- `llm.operation` - Operation type (e.g., "verb_analysis", "sentence_generation")
- `llm.request.duration_ms` - Request duration in milliseconds
- `llm.response.id` - OpenAI response ID for correlation
- `llm.usage.prompt_tokens` - Number of input tokens
- `llm.usage.completion_tokens` - Number of output tokens
- `llm.usage.total_tokens` - Total tokens used

### Error Attributes
- `llm.model` - Model name
- `llm.operation` - Operation type (if provided)
- `llm.request.duration_ms` - Request duration before failure
- `llm.error.type` - Exception type (e.g., "RateLimitError")
- `llm.error.message` - Error message

## Logging

All LLM requests are logged with structured information:

### Success Log (INFO level)
```
LLM request completed: operation=verb_analysis, model=gpt-4o-mini, duration=2345ms, 
tokens=(prompt=150, completion=75, total=225)
```

### Error Log (ERROR level)
```
LLM request failed: operation=sentence_generation, model=gpt-4o-mini, duration=1234ms, 
error=RateLimitError: Rate limit exceeded
```

## Operation Labels

The following operation labels are used throughout the service:

| Operation | Purpose |
|-----------|---------|
| `verb_analysis` | Analyzing verb conjugations and patterns |
| `verb_object_detection` | Detecting direct/indirect objects in verb usage |
| `sentence_validation` | Validating correctness of generated sentences |
| `sentence_generation` | Generating new French sentences |

## Dashboard

The "LLM Performance" dashboard in Grafana provides real-time visualization of:
- Request rates and counts
- Latency percentiles (p50, p90, p95)
- Error rates
- Token usage over time
- Cost projections (based on token usage)

## Testing

Comprehensive unit tests are located in `tests/clients/test_openai_client.py` covering:
- Metric recording for successful requests
- Span attribute setting
- Token usage tracking
- Error handling and metrics
- Logging behavior
- Edge cases (no usage data, no span recording)

Run tests with:
```bash
make test-unit
# or
poetry run pytest tests/clients/test_openai_client.py -v
```

## Notes

- The `operation` parameter is optional but recommended for better observability
- Token metrics are only recorded when OpenAI provides usage data in the response
- Span attributes are only set when a span is actively recording
- All metrics use the `environment` label for filtering by deployment stage

