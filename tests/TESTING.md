# Testing Documentation

This document provides an overview of the testing strategy, architecture, and best practices for the Language Quiz Service.

## Testing Philosophy

The project follows a **comprehensive end-to-end integration testing approach** with **real Supabase connections** and **minimal mocking**. This strategy ensures high confidence in production behavior while maintaining fast, reliable test execution.

### Core Principles

1. **Real Infrastructure**: Tests use actual Supabase instances, not mocks
2. **Minimal Mocking**: Only external LLM API calls are mocked
3. **End-to-End Coverage**: Tests validate entire request/response cycles
4. **Parallel Execution**: Tests designed for pytest-xdist compatibility
5. **Structured Error Handling**: Custom exception hierarchy with proper HTTP status codes

## Testing Strategy Evolution

### From Mock-Based to End-to-End Integration

**Previous Approach** (❌ Deprecated):
- MockSupabaseClient with complex PostgREST query translation
- Direct asyncpg database connections
- Extensive mocking of repository and service layers

**Current Approach** (✅ Current):
- Real Supabase client connections to local instances
- End-to-end request/response validation
- Only LLM calls are mocked (OpenAI, etc.)
- Tests against actual RLS policies and query translation

### Architecture Benefits

- **Production Confidence**: Tests validate actual Supabase API behavior
- **Simplified Maintenance**: No complex mock implementations to maintain
- **Real Constraint Testing**: Database constraints and RLS policies are tested
- **Performance**: 3x speedup with pytest-xdist parallel execution
- **Reliability**: No "mock drift" - tests break when real behavior changes

## Test Organization

Tests are organized by domain under `tests/<domain>/` with consistent naming:
- `test_<domain>_<component>.py` (e.g., `test_api_keys_api.py`, `test_verbs_repository.py`)

### Current Test Structure (29 test files)

#### **Core Infrastructure**
- `tests/conftest.py` - Shared fixtures and Supabase client setup
- `tests/test_main.py` - FastAPI application entry point tests
- `tests/test_security.py` - Security and authentication tests

#### **Domain-Specific Tests**

**API Keys Domain** (`tests/api_keys/`)
- `test_api_keys_api.py` - HTTP API endpoint tests
- `test_api_keys_repository.py` - Database operations tests  
- `test_api_keys_schemas.py` - Pydantic model validation tests
- `test_api_keys_service.py` - Business logic tests

**Verbs Domain** (`tests/verbs/`)
- `fixtures.py` - Verb-specific test data generators
- `test_verbs_api.py` - HTTP API endpoint tests
- `test_verbs_repository.py` - Database operations tests
- `test_verbs_schemas.py` - Pydantic model validation tests
- `test_verbs_service.py` - Business logic and LLM integration tests
- `test_verb_prompts.py` - LLM prompt template tests

**Sentences Domain** (`tests/sentences/`)
- `fixtures.py` - Sentence-specific test data generators
- `test_sentences_api.py` - HTTP API endpoint tests
- `test_sentences_repository.py` - Database operations tests
- `test_sentences_schemas.py` - Pydantic model validation tests
- `test_sentences_service.py` - Business logic and LLM integration tests
- `test_sentence_prompts.py` - LLM prompt template tests

**Problems Domain** (`tests/problems/`)
- `fixtures.py` - Problem-specific test data generators
- `test_problems_api.py` - HTTP API endpoint tests
- `test_problems_repository.py` - Database operations tests
- `test_problems_schemas.py` - Pydantic model validation tests
- `test_problems_service.py` - Business logic tests

**CLI Domain** (`tests/cli/`)
- `test_api_keys_commands.py` - API key CLI command tests
- `test_problems.py` - Problem CLI command tests
- `test_sentences.py` - Sentence CLI command tests

**Core Components** (`tests/core/`)
- `test_config.py` - Configuration and settings tests

**Database** (`tests/database/`)
- `test_database_init.py` - Database initialization tests

**Middleware** (`tests/middleware/`)
- `test_auth_middleware.py` - Authentication middleware tests

### Fixtures Catalogue

#### **Global Fixtures** (`tests/conftest.py`)
- `create_test_supabase_client()` - Supabase client factory
- Environment setup and service role key detection
- Test database configuration

#### **Domain Fixtures**

**Verbs** (`tests/verbs/fixtures.py`)
```python
# Data generators for verb testing
generate_random_verb_data() -> Dict[str, Any]
generate_random_conjugation_data() -> Dict[str, Any]
generate_unique_verb_infinitive() -> str
```

**Sentences** (`tests/sentences/fixtures.py`)
```python
# Data generators for sentence testing  
generate_random_sentence_data() -> Dict[str, Any]
generate_sentence_with_verb(verb_id: UUID) -> Dict[str, Any]
```

**Problems** (`tests/problems/fixtures.py`)
```python
# Data generators for problem testing
generate_random_problem_data() -> Dict[str, Any]
generate_grammar_problem_constraints() -> GrammarProblemConstraints
```

### Test Data Management

#### **Pre-seeded Test Data**

Critical test data is pre-seeded via `sql/test/` scripts:

- **`sql/test/1-LoadTestKeys.sql`**: API keys for authentication testing
  - `sk_live_test_read_key` - Read-only permissions
  - `sk_live_test_write_key` - Write permissions  
  - `sk_live_test_admin_key` - Admin permissions
- **`sql/test/2-LoadTestVerbs.sql`**: Baseline verbs for conflict testing
  - Common French verbs (être, avoir, parler, etc.)
  - Used for uniqueness constraint testing

#### **Dynamic Test Data Generation**

Most test data is generated dynamically to ensure isolation:

```python
# Domain-specific generators with UUID suffixes for parallel safety
from tests.verbs.fixtures import generate_random_verb_data
from tests.sentences.fixtures import generate_random_sentence_data
from tests.problems.fixtures import generate_random_problem_data

# Usage in tests - always ensure uniqueness
verb_data = VerbCreate(**generate_random_verb_data())
verb_data.infinitive = f"test_{uuid4().hex[:8]}"  # Parallel-safe
```

## Test Types & Coverage

Tests follow a domain and type driven naming pattern where possible:

#### **API Layer Tests** (`test_*_api.py`)
- **End-to-End HTTP Testing**: Full request/response cycles
- **Authentication & Authorization**: Real API key validation
- **Error Handling**: Structured exception responses (404, 400, 503, etc.)
- **Performance**: Parallel execution with pytest-xdist
- **Validation**: Pydantic schema validation of responses

#### **Service Layer Tests** (`test_*_service.py`)
- **Business Logic**: Core application logic validation
- **Integration Testing**: Real repository connections
- **Exception Handling**: Custom exception hierarchy testing
- **LLM Integration**: Mocked OpenAI calls only
- **Data Orchestration**: Multi-service coordination

#### **Repository Layer Tests** (`test_*_repository.py`)
- **Database Integration**: Real Supabase client operations
- **CRUD Operations**: Create, Read, Update, Delete with constraints
- **Query Translation**: PostgREST query building validation
- **Error Scenarios**: Database constraint violations
- **Performance**: Optimized for parallel execution

#### **Schema Tests** (`test_*_schemas.py`)
- **Pydantic Validation**: Request/response model validation
- **Data Transformation**: Enum serialization, UUID handling
- **Edge Cases**: Invalid data rejection
- **Backward Compatibility**: Schema evolution testing

## Parallel Execution with pytest-xdist

### Performance Improvements
- **7-8x Speedup**: ~12 seconds vs ~90 seconds single-threaded
- **Auto-scaling**: `pytest -n auto` detects optimal worker count
- **Test Isolation**: Each worker operates independently

### Compatibility Requirements
- **Unique Test Data**: Dynamic UUID generation for unique identifiers
- **Database Isolation**: Each test creates unique entities
- **No Global State**: Tests don't depend on execution order
- **Runtime Generation**: Dynamic data created at execution time, not collection time

### Example: Parallel-Safe Test Pattern
```python
@pytest.mark.asyncio
async def test_create_unique_verb(verb_service):
    """Test creating a verb with parallel-safe unique data."""
    from uuid import uuid4
    
    # Generate unique data at runtime (not collection time)
    verb_data = VerbCreate(**generate_random_verb_data())
    verb_data.infinitive = f"test_verb_{uuid4().hex[:8]}"
    
    # Test against real Supabase instance
    created_verb = await verb_service.create_verb(verb_data)
    assert created_verb.infinitive == verb_data.infinitive
```

## Exception Handling & Error Testing

### Structured Exception Hierarchy

The application uses a comprehensive custom exception system:

```python
AppException (base)
├── NotFoundError (404)
├── ValidationError (400) 
├── ContentGenerationError (503)
├── RepositoryError (500)
├── ServiceError (500)
└── LanguageResourceNotFoundError (404)
```

### Testing Exception Scenarios

**API Layer Exception Testing**:
```python
def test_verb_not_found_returns_404(client, read_headers):
    """Test that missing verbs return proper 404 responses."""
    response = client.get("/api/v1/verbs/nonexistent", headers=read_headers)
    assert response.status_code == 404
    assert response.json()["error"] is True
    assert "not found" in response.json()["message"].lower()
```

**Service Layer Exception Testing**:
```python
@pytest.mark.asyncio
async def test_invalid_verb_raises_content_generation_error(verb_service):
    """Test that invalid LLM responses raise proper exceptions."""
    with pytest.raises(ContentGenerationError) as exc_info:
        await verb_service.download_verb("invalidverb123")
    assert "not a valid french verb" in str(exc_info.value)
```

## Test Data Management

### Pre-seeded Test Data

Critical test data is pre-seeded via `sql/test/` scripts:

- **`sql/test/1-LoadTestKeys.sql`**: API keys for authentication testing
- **`sql/test/2-LoadTestVerbs.sql`**: Baseline verbs for conflict testing

### Dynamic Test Data Generation

Most test data is generated dynamically to ensure isolation:

```python
# Domain-specific generators
from tests.verbs.fixtures import generate_random_verb_data
from tests.sentences.fixtures import generate_random_sentence_data
from tests.problems.fixtures import generate_random_problem_data

# Usage in tests
verb_data = VerbCreate(**generate_random_verb_data())
verb_data.infinitive = f"test_{uuid4().hex[:8]}"  # Ensure uniqueness
```

## Domain-Specific Testing Patterns

### Verbs Domain

**Uniqueness Testing**: Verbs identified by 4-tuple `(infinitive, auxiliary, reflexive, target_language_code)`
```python
def test_verb_uniqueness_constraint(verb_service):
    """Test that duplicate verbs raise appropriate errors."""
    # Test expects "parler" to exist in pre-seeded data
    with pytest.raises(ContentGenerationError) as exc_info:
        await verb_service.download_verb("parler")  # Already exists
    assert "already exists" in str(exc_info.value)
```

**LLM Integration Testing**: Only mock external API calls
```python
def test_download_verb_with_mocked_llm(client, write_headers):
    """Test verb download with mocked LLM responses."""
    with patch("src.services.verb_service.OpenAIClient") as mock_client:
        mock_client.return_value.handle_request = AsyncMock(
            side_effect=[
                json.dumps({"infinitive": "tester", "auxiliary": "avoir", ...}),
                json.dumps({"can_have_cod": True, "can_have_coi": False})
            ]
        )
        response = client.post("/api/v1/verbs/download", 
                             json={"infinitive": "tester"}, headers=write_headers)
        assert response.status_code == 201
```

### API Keys Domain

**Authentication Testing**: Real API key validation against Supabase
```python
def test_invalid_api_key_returns_401(client):
    """Test authentication with invalid API key."""
    headers = {"X-API-Key": "sk_live_invalid_key"}
    response = client.get("/api/v1/verbs/random", headers=headers)
    assert response.status_code == 401
    assert "invalid api key" in response.json()["message"].lower()
```

### Problems Domain

**Complex Business Logic**: Multi-service integration testing
```python
@pytest.mark.asyncio
async def test_create_grammar_problem_integration(problem_service):
    """Test grammar problem creation with verb and sentence integration."""
    constraints = GrammarProblemConstraints(
        tenses=[Tense.PRESENT],
        pronouns=[Pronoun.FIRST_PERSON]
    )
    problem = await problem_service.create_random_grammar_problem(
        constraints=constraints, statement_count=4
    )
    assert len(problem.statements) == 4
    assert problem.correct_answer_index < 4
```

## Running Tests

### Full Suite (Parallel Execution)
```bash
# Auto-detect optimal worker count
pytest -n auto

# Specific worker count
pytest -n 4

# Single-threaded (for debugging)
pytest
```

### Domain-Specific Testing
```bash
pytest tests/verbs/ -n auto      # Verb domain with parallel execution
pytest tests/api_keys/ -v        # API keys with verbose output
pytest tests/sentences/ --tb=short  # Sentences with short traceback
```

### Coverage Analysis
```bash
pytest --cov=src --cov-report=html --cov-fail-under=80
```

### Performance Testing
```bash
# Compare single-threaded vs parallel performance
time pytest
time pytest -n auto
```

## CI/CD Integration

### GitHub Actions Configuration
- **Parallel Execution**: Utilizes pytest-xdist for fast CI runs
- **Supabase Integration**: Real database testing in CI environment
- **Coverage Enforcement**: 80% minimum threshold
- **Environment Variables**: Automatic Supabase configuration

### Environment Setup
```bash
# Required environment variables (set automatically in CI)
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_SERVICE_ROLE_KEY=<auto-detected>
SUPABASE_ANON_KEY=<auto-detected>
```

## Migration Guide

### Updating Existing Tests

**1. Remove Complex Mocks**:
```python
# ❌ Old approach - Complex MockSupabaseClient
mock_client = MockSupabaseClient()
# ... 50 lines of mock setup

# ✅ New approach - Real Supabase connection
# Tests use actual service dependencies automatically
```

**2. Use Real Error Scenarios**:
```python
# ❌ Old approach - Mock error responses
mock_client.get_verb.side_effect = Exception("Mock error")

# ✅ New approach - Trigger real constraint violations
await verb_service.create_verb(duplicate_verb_data)  # Raises RepositoryError
```

**3. Make Tests Parallel-Safe**:
```python
# ❌ Old approach - Hardcoded test data
verb_data.infinitive = "test_verb"  # Conflicts in parallel execution

# ✅ New approach - Dynamic unique data
verb_data.infinitive = f"test_verb_{uuid4().hex[:8]}"
```

### Best Practices

1. **Test Real Behavior**: Prefer triggering actual application flows over mocking
2. **Unique Data**: Always generate unique identifiers for test entities
3. **Exception Testing**: Test the full exception → HTTP status code flow
4. **Parallel Safety**: Ensure tests don't interfere when run simultaneously
5. **LLM-Only Mocking**: Only mock external API calls (OpenAI, etc.)

## Performance Metrics

### Current Test Performance
- **Total Test Files**: 29 files across 9 domains
- **Test Structure**: API, Repository, Service, Schema layers per domain
- **Coverage**: Maintained above 80% threshold
- **Execution**: Optimized for parallel execution with pytest-xdist
- **Database**: Real Supabase integration in CI/CD and local development

### Test Distribution by Domain
- **API Keys**: 4 test files (API, Repository, Service, Schema)
- **Verbs**: 6 test files (API, Repository, Service, Schema, Prompts, Fixtures)
- **Sentences**: 6 test files (API, Repository, Service, Schema, Prompts, Fixtures)  
- **Problems**: 5 test files (API, Repository, Service, Schema, Fixtures)
- **CLI**: 3 test files (Commands for different domains)
- **Core**: 5 test files (Config, Security, Main, Database, Middleware)

## Troubleshooting

### Common Issues

**1. Parallel Execution Failures**:
```bash
# Check for hardcoded test data causing conflicts
grep -r "test_.*=" tests/ | grep -v uuid4

# Fix by adding UUID suffixes
test_name = f"test_entity_{uuid4().hex[:8]}"
```

**2. Supabase Connection Issues**:
```bash
# Verify local Supabase is running
supabase status
supabase start  # If not running
```

**3. Authentication Failures**:
```bash
# Reset and reload test data
supabase db reset
./scripts/load-schemas.sh
```

**4. Coverage Drops**:
```bash
# Run with coverage analysis
pytest --cov=src --cov-report=term-missing
```

### Debug Techniques

1. **Isolated Test Runs**: Run single tests to isolate issues
2. **Verbose Output**: Use `-v` flag for detailed test information
3. **Exception Details**: Use `--tb=long` for full stack traces
4. **Worker Isolation**: Use `-n 1` to test single-worker behavior

This testing architecture provides a robust foundation for maintaining high code quality while ensuring fast, reliable test execution in both development and CI/CD environments. 