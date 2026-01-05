# Development Guide

This document covers common development workflows, CLI commands, and operational procedures for the Language Quiz Service.

## Prerequisites

- **Python 3.11+**
- **Poetry** - Dependency management
- **Supabase CLI** - Local database
- **Docker** - For containerized development (optional)

```bash
# Install dependencies
poetry install

# Start local Supabase
make start-supabase
```

---

## Quick Reference

### Start Development Stack

```bash
docker-compose up -d
```

This:
1. Uses local Supabase automatically
2. Starts FastAPI with auto-reload on http://localhost:8000
3. Starts background workers (if `WORKER_COUNT > 0`)

### Run Tests

```bash
make test              # All tests (excluding acceptance)
make test-cov          # With coverage report
make test-acceptance   # Acceptance tests against running service
```

---

## CLI Overview

The `lqs` CLI defaults to **local Supabase**. Use `--remote` for production operations.

```bash
lqs <command>           # Uses local Supabase (default)
lqs --remote <command>  # Uses SERVICE_URL from environment
```

### Command Groups

| Group | Purpose |
|-------|---------|
| `database` | Database initialization and cleanup |
| `problem` | Problem management and generation |
| `generation-request` | Async generation request tracking |
| `cache` | Cache statistics and reload |
| `verb` | Verb data management |
| `sentence` | Sentence generation |
| `api-keys` | API key management |

---

## Common Workflows

### 1. Fresh Database Reset

When you need to start with a clean database:

```bash
# Reset Supabase (wipes everything, applies migrations, runs seed.sql)
supabase db reset

# Initialize verbs and conjugations
lqs database init
```

### 2. Clean Test Data Only

Remove test artifacts without affecting production data:

```bash
lqs database clean
```

This removes:
- Test verbs (those with `_` in infinitive)
- Test problems (tagged with `test_data`)
- Test generation requests (with `test_data` in metadata)

### 3. Purge Problems Only

Delete all problems while keeping verbs/conjugations:

```bash
lqs problem purge                    # Delete all problems
lqs problem purge --topic test_data  # Delete only test problems
```

### 4. Problem Generation Workflow

**Complete flow from generation to verification:**

```bash
# Step 1: Trigger async generation
lqs problem generate -c 5

# Step 2: Note the generation request ID from output
# Output: ✅ Enqueued 5 problem generation requests (request_id: abc123...)

# Step 3: Check generation progress
lqs generation-request status abc123...

# Step 4: View generated problems
lqs problem get --generation-id abc123...

# Step 5: Inspect a specific problem
lqs problem get --id <problem-id> --verbose
```

### 5. Problem Lifecycle: By Generation Request

Manage all problems from a single generation request:

```bash
# View what was generated
lqs problem get --generation-id <generation-id>

# Delete all problems from a failed/bad generation
lqs problem delete --generation-id <generation-id>

# Force delete (skip confirmation)
lqs problem delete --generation-id <generation-id> -f
```

### 6. Problem Lifecycle: Individual Problem

Manage a single problem:

```bash
# View problem details
lqs problem get --id <problem-id>
lqs problem get --id <problem-id> --verbose

# Delete a specific problem
lqs problem delete --id <problem-id>
lqs problem delete --id <problem-id> -f  # Skip confirmation
```

### 7. Generation Request Maintenance

```bash
# List recent requests
lqs generation-request list
lqs generation-request list --status processing
lqs generation-request list --status completed

# Check specific request with problem details
lqs generation-request status <request-id>

# Clean old requests (older than 7 days by default)
lqs generation-request clean
lqs generation-request clean --older-than 14
```

### 8. Cache Management

After direct database changes (via Supabase dashboard or SQL):

```bash
# View cache stats
lqs cache stats

# Reload all caches
lqs cache reload

# Reload specific cache
lqs cache reload verbs
lqs cache reload conjugations
lqs cache reload api-keys
```

---

## Database Commands

### `lqs database init`

Initialize the database with verbs and conjugations:

```bash
lqs database init
```

### `lqs database clean`

Clean up test data:

```bash
lqs database clean
```

### `lqs database wipe`

**WARNING**: Deletes ALL data from local database.

```bash
lqs database wipe
```

This command is **forbidden** with `--remote` for safety.

---

## Problem Commands

### `lqs problem generate`

Trigger async problem generation:

```bash
lqs problem generate                     # Generate 1 problem
lqs problem generate -c 10               # Generate 10 problems
lqs problem generate -s 5                # 5 statements per problem
lqs problem generate --include-negation  # Force negation
lqs problem generate --tense present     # Specific tense
```

### `lqs problem random`

Get a random problem from the database:

```bash
lqs problem random
lqs problem random --json  # JSON output
```

### `lqs problem list`

List problems with optional filtering:

```bash
lqs problem list
lqs problem list --type grammar
lqs problem list --topic negation
lqs problem list --limit 50
```

### `lqs problem get`

Retrieve problem(s) by ID or generation request:

```bash
# Get single problem
lqs problem get --id <problem-id>
lqs problem get --id <problem-id> --verbose

# Get all problems from a generation request
lqs problem get --generation-id <generation-id>
lqs problem get --generation-id <generation-id> --json
```

### `lqs problem stats`

Show problem statistics:

```bash
lqs problem stats
```

### `lqs problem delete`

Delete problem(s) by ID or generation request:

```bash
# Delete single problem
lqs problem delete --id <problem-id>
lqs problem delete --id <problem-id> -f  # Skip confirmation

# Delete all problems from a generation request
lqs problem delete --generation-id <generation-id>
lqs problem delete --generation-id <generation-id> -f
```

### `lqs problem purge`

Delete all problems (or filtered):

```bash
lqs problem purge                    # All problems
lqs problem purge --topic test_data  # Only matching topic
lqs problem purge -f                 # Skip confirmation
```

### `lqs sentence purge --orphaned`

Delete orphaned sentences that are not referenced by any problem:

```bash
lqs sentence purge --orphaned              # Delete orphaned sentences
lqs sentence purge --orphaned -f           # Skip confirmation
```

Orphaned sentences can occur if the service restarts during problem generation, leaving sentences without their corresponding problems.

---

## Generation Request Commands

### `lqs generation-request list`

List generation requests:

```bash
lqs generation-request list
lqs generation-request list --status pending
lqs generation-request list --status completed
lqs generation-request list --limit 50
```

### `lqs generation-request status`

Get detailed status:

```bash
lqs generation-request status <request-id>
```

### `lqs generation-request clean`

Delete old completed/failed requests:

```bash
lqs generation-request clean              # Older than 7 days
lqs generation-request clean --older-than 14
```

---

## Cache Commands

### `lqs cache stats`

View cache statistics:

```bash
lqs cache stats
```

Output includes:
- Load status
- Entry counts
- Hit/miss counts
- Hit rate percentage

### `lqs cache reload`

Force reload caches from database:

```bash
lqs cache reload              # All caches
lqs cache reload verbs        # Verb cache only
lqs cache reload conjugations # Conjugation cache only
lqs cache reload api-keys     # API key cache only
```

---

## API Key Commands

### `lqs api-keys create`

Create a new API key:

```bash
lqs api-keys create --name "My Key" --permissions read,write
```

### `lqs api-keys list`

List all API keys:

```bash
lqs api-keys list
```

### `lqs api-keys revoke`

Revoke an API key:

```bash
lqs api-keys revoke <key-id>
```

---

## Environment Variables

### Required for Development

```bash
OPENAI_API_KEY=sk-...           # OpenAI API access
```

### Optional

```bash
SERVICE_URL=https://...          # Remote service URL (for --remote)
SERVICE_API_KEY=sk_live_...      # API key for remote access
WORKER_COUNT=2                   # Background workers (0 to disable)
LOG_LEVEL=DEBUG                  # Logging verbosity
```

---

## Makefile Targets

```bash
make help              # Show all targets

# Development
make setup             # First-time setup
make dev               # Start with local Supabase
make dev-monitored     # Start with Grafana observability

# Testing
make test              # Run tests
make test-cov          # With coverage
make test-acceptance   # Acceptance tests

# Code Quality
make lint              # Lint code
make format            # Format code
make lint-check        # Check without fixing

# Deployment
make deploy ENV=staging
make deploy ENV=production

# Observability
make dashboards-deploy
make dashboards-validate
```

---

## Troubleshooting

### Supabase Not Running

```bash
supabase start
# Or with minimal containers:
make start-supabase
```

### Cache Out of Sync

After direct database changes:

```bash
lqs cache reload
```

Or restart the service to reload caches at startup.

### Generation Requests Stuck

Check Kafka connectivity and worker status:

```bash
# Check worker logs
make logs

# List stuck requests
lqs generation-request list --status processing
```

### API Key Issues

```bash
# List keys
lqs api-keys list

# Reload API key cache
lqs cache reload api-keys
```

