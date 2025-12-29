# Generation Trace Implementation Guide

## Overview

This implementation adds comprehensive generation trace capture to the problem generation pipeline. Every problem now stores full metadata about how it was generated, including:

- **Model information**: Which model, prompt version, response IDs
- **Token usage**: Input, output, reasoning tokens for cost tracking
- **Reasoning traces**: Full chain-of-thought from gpt-5 models
- **Full prompts**: The exact prompts sent to the LLM
- **Quality tracking**: Status and issues for future review workflows

## Files to Integrate

### 1. Database Migration

**File**: `generation_trace_migration.sql`
**Destination**: `supabase/migrations/YYYYMMDDHHMMSS_add_generation_trace.sql`

```bash
# Copy to migrations folder with timestamp
cp generation_trace_migration.sql supabase/migrations/$(date +%Y%m%d%H%M%S)_add_generation_trace.sql

# Apply migration
supabase db push
```

### 2. LLM Response Schema

**File**: `llm_response.py`  
**Destination**: `src/schemas/llm_response.py`

This adds three new dataclasses:
- `LLMResponse` - Rich response from OpenAI with metadata
- `SentenceGenerationTrace` - Per-sentence trace data
- `ProblemGenerationTrace` - Aggregated problem-level trace

### 3. OpenAI Client Update

**File**: `openai_client_updated.py`
**Destination**: Update `src/clients/openai_client.py`

Key changes:
- Add `handle_request_with_metadata()` method returning `LLMResponse`
- Extract `reasoning_content` and `reasoning_tokens` from gpt-5 responses
- Keep `handle_request()` for backward compatibility

```python
# The existing method now delegates to the new one:
async def handle_request(...) -> str:
    response = await self.handle_request_with_metadata(...)
    return response.content
```

### 4. Problem Schema Update

**File**: `schemas_problems_updated.py`
**Destination**: Update `src/schemas/problems.py`

Add `generation_trace: dict[str, Any] | None` field to:
- `ProblemBase`
- `ProblemCreate`
- `Problem`

### 5. Sentence Service Update

**File**: `sentence_service_updated.py`
**Destination**: Update `src/services/sentence_service.py`

Add new method:
```python
async def generate_sentence_with_trace(...) -> tuple[Sentence, SentenceGenerationTrace]:
```

### 6. Problem Service Update

**File**: `problem_service_updated.py`
**Destination**: Update `src/services/problem_service.py`

Modify `create_random_grammar_problem()` to:
1. Use `generate_sentence_with_trace()` for each sentence
2. Aggregate traces into `ProblemGenerationTrace`
3. Include `generation_trace=trace.to_dict()` in `ProblemCreate`

### 7. CLI Commands (Optional)

**File**: `cli_trace_commands.py`
**Destination**: Add to `src/cli/problems/`

Adds inspection commands:
- `quiz problem inspect <id> --show-reasoning`
- `quiz problem trace-stats`
- `quiz problem find-issues --quality-status pending_review`

### 8. Tests

**File**: `tests_generation_trace.py`
**Destination**: `tests/schemas/test_llm_response.py`

## Integration Steps

### Step 1: Apply Migration

```bash
cd language-quiz-service
cp /path/to/generation_trace_migration.sql supabase/migrations/$(date +%Y%m%d%H%M%S)_add_generation_trace.sql
supabase db push
```

### Step 2: Add Schema File

```bash
cp /path/to/llm_response.py src/schemas/llm_response.py
```

### Step 3: Update OpenAI Client

In `src/clients/openai_client.py`:

1. Add import: `from src.schemas.llm_response import LLMResponse`
2. Add `handle_request_with_metadata()` method
3. Update `handle_request()` to delegate

### Step 4: Update Problem Schema

In `src/schemas/problems.py`:

1. Add to `ProblemBase`:
```python
generation_trace: dict[str, Any] | None = Field(
    None, 
    description="Full generation trace including reasoning, prompts, and quality info"
)
```

### Step 5: Update Sentence Service

In `src/services/sentence_service.py`:

1. Add imports for trace classes
2. Add `SENTENCE_PROMPT_VERSION = "2.0"` constant
3. Add `generate_sentence_with_trace()` method

### Step 6: Update Problem Service

In `src/services/problem_service.py`:

1. Add imports for trace classes
2. Add `PROBLEM_PROMPT_VERSION = "2.0"` constant
3. Modify `create_random_grammar_problem()` to capture traces
4. Update `_package_grammar_problem()` to accept `generation_trace` parameter

### Step 7: Run Tests

```bash
pytest tests/schemas/test_llm_response.py -v
pytest tests/ -k "generation_trace" -v
```

### Step 8: Verify End-to-End

```bash
# Generate a problem
quiz problem new --display

# Inspect the trace
quiz problem inspect <problem_id> --show-reasoning
```

## Checking Reasoning Content

To verify reasoning is being captured, check your logs for:

```
LLM request completed: operation=sentence_generation, model=gpt-5-nano-2025-08-07, 
duration=1234ms, tokens=(prompt=150, completion=75, total=225, reasoning_tokens=500)
```

The `reasoning_tokens` value indicates reasoning content was captured.

## Querying Traces in SQL

```sql
-- Find problems with high reasoning token usage
SELECT 
    id,
    title,
    generation_trace->>'total_reasoning_tokens' as reasoning_tokens,
    generation_trace->>'model' as model
FROM problems
WHERE (generation_trace->>'total_reasoning_tokens')::int > 1000
ORDER BY (generation_trace->>'total_reasoning_tokens')::int DESC;

-- Find problems needing review
SELECT id, title, created_at
FROM problems
WHERE generation_trace->>'quality_status' = 'pending_review';

-- Analyze token usage by model
SELECT 
    generation_trace->>'model' as model,
    COUNT(*) as problem_count,
    AVG((generation_trace->>'total_tokens')::int) as avg_tokens
FROM problems
WHERE generation_trace IS NOT NULL
GROUP BY generation_trace->>'model';
```

## Future Enhancements

With traces captured, you can now:

1. **Add self-review**: Parse reasoning content for quality signals
2. **Build a judge**: Use traces to train a quality classifier
3. **A/B test prompts**: Compare outputs across prompt versions
4. **Cost analysis**: Track token usage trends over time
5. **Debug bizarre outputs**: See exactly what the model was thinking

## Storage Considerations

At current estimates:
- ~5-10KB per problem (with full prompts and reasoning)
- 1,000 problems = 5-10MB
- 10,000 problems = 50-100MB

This is well within PostgreSQL JSONB capabilities. If storage becomes a concern later:
1. Move `prompt_text` to a separate table or drop it
2. Truncate `reasoning_content` to first N characters
3. Archive old traces to cold storage
