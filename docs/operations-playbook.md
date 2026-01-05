# Operations Playbook

This playbook documents common operational tasks for the Language Quiz Service using the `lqs` CLI.

## Table of Contents

- [Problem Retrieval](#problem-retrieval)
  - [Piping and Streaming](#piping-and-streaming)
- [Reviewing LLM Reasoning](#reviewing-llm-reasoning)
- [Bulk Deletion Operations](#bulk-deletion-operations)
  - [Problem Cleanup](#problem-cleanup)
  - [Generation Request Cleanup](#generation-request-cleanup)
- [Quick Reference](#quick-reference)

---

## Problem Retrieval

### Single Problem Fetch

```bash
# Get a problem by ID
lqs problem get 123e4567-e89b-12d3-a456-426614174000

# Get with verbose details
lqs problem get 123e4567-e89b-12d3-a456-426614174000 -v

# Get with LLM generation trace (prompts, reasoning, token usage)
lqs problem get 123e4567-e89b-12d3-a456-426614174000 --llm-trace
```

### Generation Request Fetch

```bash
# Get a generation request with all its problems
lqs generation-request get 550e8400-e29b-41d4-a716-446655440000

# Get with verbose problem details
lqs generation-request get 550e8400-e29b-41d4-a716-446655440000 -v

# Get as JSON for piping
lqs generation-request get 550e8400-e29b-41d4-a716-446655440000 --json
```

### Piping and Streaming

The CLI supports piping UUIDs (one per line) for batch operations. This enables powerful command chaining.

#### Get Problems from a Generation Request

After running `lqs problem generate`, get the completed problems:

```bash
# Get generation request output, extract problem IDs, fetch each problem
lqs generation-request get 1289c46d-16b0-4a39-9138-4302fed9b6d7 --json \
  | jq -r '.entities[].id' \
  | lqs problem get
```

#### List and Fetch Multiple Problems

```bash
# List all problems, then fetch full details for each
lqs problem list --json | jq -r '.problems[].id' | lqs problem get

# List grammar problems, get full details
lqs problem list --type grammar --json | jq -r '.problems[].id' | lqs problem get

# Get first 5 problems with details
lqs problem list --json | jq -r '.problems[:5][].id' | lqs problem get
```

#### Export Problems as JSONL

```bash
# Export all problems as JSONL (one JSON object per line)
lqs problem list --json | jq -r '.problems[].id' | lqs problem get --json > problems.jsonl

# Export with full metadata including generation trace
lqs problem list --json | jq -r '.problems[].id' | lqs problem get --json --llm-trace > problems-with-trace.jsonl
```

#### Delete by Filtered List

```bash
# Delete all grammar problems older than a week (uses purge instead)
lqs problem purge --older-than 7d --force

# Delete specific problems by piping IDs
lqs problem list --type vocabulary --json | jq -r '.problems[].id' | lqs problem delete -f
```

---

## Reviewing LLM Reasoning

The `--llm-trace` flag includes the LLM generation trace with prompts, reasoning content, and token usage. This is essential for debugging generation quality and understanding model behavior.

### View Reasoning for a Single Problem

```bash
# Get problem with full LLM trace
lqs problem get <uuid> --llm-trace

# Output as JSON for inspection
lqs problem get <uuid> --llm-trace --json | jq '.generation_trace'
```

### Extract Reasoning from a Generation Batch

Get reasoning summaries for all problems from a generation request:

```bash
# Extract key reasoning fields grouped by problem
lqs generation-request get <generation-id> --json \
  | jq -r '.entities[].id' \
  | lqs problem get --llm-trace --json \
  | jq -s '[.[] | {
      problem_id: .id,
      sentences: [.generation_trace.sentences[] | {
        prompt_text,
        reasoning_content,
        reasoning_tokens,
        generation_time_ms
      }]
    }]'
```

### Analyze Token Usage

```bash
# Get total tokens used per problem
lqs generation-request get <generation-id> --json \
  | jq -r '.entities[].id' \
  | lqs problem get --llm-trace --json \
  | jq -s '[.[] | {
      problem_id: .id,
      total_reasoning_tokens: ([.generation_trace.sentences[].reasoning_tokens] | add),
      total_generation_ms: ([.generation_trace.sentences[].generation_time_ms] | add)
    }]'
```

### Compare Model Reasoning

```bash
# Extract just the reasoning content for review
lqs problem get <uuid> --llm-trace --json \
  | jq '.generation_trace.sentences[] | .reasoning_content'
```

---

## Bulk Deletion Operations

### Problem Cleanup

The `lqs problem purge` command provides efficient bulk deletion with flexible filtering.

#### Delete Problems by Age

```bash
# Delete problems older than 7 days
lqs problem purge --older-than 7d --force

# Delete problems older than 2 weeks
lqs problem purge --older-than 2w --force

# Delete problems created before a specific date
lqs problem purge --older-than 2025-01-01 --force
```

#### Delete Problems in a Date Range

```bash
# Delete problems created between 7 days and 1 day ago
lqs problem purge --newer-than 7d --older-than 1d --force
```

#### Delete Problems by Topic

```bash
# Delete all problems tagged with "test_data"
lqs problem purge --topic test_data --force

# Delete problems with multiple topic tags
lqs problem purge --topic test_data --topic cleanup --force
```

#### Combined Filters

```bash
# Delete test problems older than 2 days
lqs problem purge --older-than 2d --topic test_data --force

# Delete old test problems in a specific date range
lqs problem purge --newer-than 30d --older-than 7d --topic test_data --force
```

#### Interactive Mode (Dry Run)

Omit `--force` to see what will be deleted and confirm:

```bash
# Shows count and asks for confirmation
lqs problem purge --older-than 7d

# Example output:
# 🎯 Found 42 problems with created before 2025-01-01 12:00
# ⚠️  This will delete 42 problems.
# Continue? [y/N]:
```

---

### Generation Request Cleanup

Use `lqs generation-request clean` to remove old completed, failed, or expired generation requests.

#### Basic Cleanup

```bash
# Delete completed/failed requests older than 7 days
lqs generation-request clean --older-than 7d --force

# Delete requests older than 24 hours
lqs generation-request clean --older-than 24h --force
```

#### Filter by Topic

```bash
# Delete old test generation requests
lqs generation-request clean --older-than 1d --topic test_data --force
```

---

## Quick Reference

### Problem Retrieval

| Task | Command |
|------|---------|
| Get problem by ID | `lqs problem get <uuid>` |
| Get generation request | `lqs generation-request get <uuid>` |
| Get with verbose details | `lqs problem get <uuid> -v` |
| Get with LLM trace | `lqs problem get <uuid> --llm-trace` |
| Extract reasoning from batch | `lqs generation-request get <uuid> --json \| jq ... \| lqs problem get --llm-trace --json` |
| Pipe IDs to fetch | `... \| jq -r '.problems[].id' \| lqs problem get` |
| Export as JSONL | `... \| lqs problem get --json > out.jsonl` |

### Deletion

| Task | Command |
|------|---------|
| Delete problems older than N days | `lqs problem purge --older-than Nd -f` |
| Delete test problems | `lqs problem purge --topic test_data -f` |
| Delete old test problems | `lqs problem purge --older-than 2d --topic test_data -f` |
| Delete problems in date range | `lqs problem purge --newer-than 7d --older-than 1d -f` |
| Delete problems before date | `lqs problem purge --older-than 2025-01-01 -f` |
| Delete by piped IDs | `... \| jq -r '.problems[].id' \| lqs problem delete -f` |
| Clean old generation requests | `lqs generation-request clean --older-than 7d -f` |
| Preview deletion (no --force) | `lqs problem purge --older-than 7d` |

### Duration Formats

The `--older-than` and `--newer-than` options accept:

| Format | Example | Meaning |
|--------|---------|---------|
| Minutes | `30m` | 30 minutes ago |
| Hours | `2h` | 2 hours ago |
| Days | `7d` | 7 days ago |
| Weeks | `2w` | 2 weeks ago |
| Combined | `1d12h` | 1 day and 12 hours ago |
| Absolute date | `2025-01-01` | January 1, 2025 |
| Absolute datetime | `2025-01-01T12:00:00` | January 1, 2025 at noon UTC |

### Safety Notes

- **Remote purge is forbidden**: The `purge` command only works on local databases for safety.
- **Always preview first**: Run without `--force` to see what will be deleted.
- **Use topic tags**: Tag test data with `test_data` for easy cleanup.
