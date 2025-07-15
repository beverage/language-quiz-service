# Testing Documentation

This document provides an overview of the testing structure, test cases, and fixtures for the Language Quiz Service.

## Testing Strategy

The project uses a **testcontainers-based integration testing approach** with **direct database calls** via asyncpg for robust, fast, and reliable testing. This eliminates the complexity of mocking Supabase API calls and provides comprehensive business logic testing against real database constraints.

### Key Components

1. **Testcontainers**: Real PostgreSQL database in Docker for each test session
2. **Direct Database Calls**: asyncpg connections for fast, reliable database operations  
3. **Domain-Specific DB Helpers**: High-level database operations using domain objects
4. **Data Generation Fixtures**: Reusable test data generators separate from database operations

## Test Organization

Tests are organized by domain under `tests/<domain>/` with the following file naming pattern:
- `test_<domain>_<component>.py` (e.g., `test_api_keys_schemas.py`, `test_api_keys_repository.py`)

### Test Types

- **Unit Tests**: Pydantic schema validation, business logic  
- **Integration Tests**: Repository operations with real PostgreSQL database via testcontainers
- **API Tests**: FastAPI endpoint testing
- **Service Tests**: Business service layer testing

### Architecture Benefits

- **Fast**: Direct database calls are faster than API translation layers
- **Reliable**: Real database constraints catch edge cases and violations
- **Simple**: No complex PostgREST query translation mocking required
- **Comprehensive**: Full business logic testing with actual database behavior

## Directory of Test Cases by Domain

### Core Domain
- **tests/core/test_config.py**
  - Configuration loading and validation
  - Environment variable handling

### Database Domain  
- **tests/database/test_database_init.py**
  - Database initialization and migration tests

### Verbs Domain
- **tests/verbs/test_verbs_schemas.py**
  - VerbCreate, VerbUpdate schema validation
  - Enum handling (VerbType, Transitivity)
  - Language code validation
  
- **tests/verbs/test_verbs_repository.py**
  - CRUD operations (create, get, update, delete)
  - Filtering and search functionality
  - Pagination and bulk operations
  - Database constraint enforcement
  - Edge cases and error handling
  
- **tests/verbs/test_verbs_service.py**
  - Business logic validation
  - External API integrations
  
- **tests/verbs/test_verbs_api.py**
  - HTTP endpoint testing
  - Request/response validation
  
- **tests/verbs/test_verb_prompts.py**
  - AI prompt generation for verb conjugations

### Sentences Domain
- **tests/sentences/test_sentences_schemas.py**
  - SentenceCreate, SentenceUpdate schema validation
  - Enum handling (Pronoun, Tense, DirectObject, IndirectObject, Negation)
  - Language code validation
  
- **tests/sentences/test_sentences_repository.py**
  - CRUD operations with foreign key constraints
  - Complex filtering (verb, correctness, tense, pronoun combinations)
  - Random sentence retrieval with filters
  - Counting operations
  - Partial field updates
  - Cascade deletion behavior
  - Multiple verb handling
  - Language code filtering
  - Error handling and edge cases
  
- **tests/sentences/test_sentences_service.py**
  - Business logic validation
  - AI sentence generation
  - Validation pipeline integration
  
- **tests/sentences/test_sentences_api.py**
  - HTTP endpoint testing
  - Request/response validation
  
- **tests/sentences/test_sentence_prompts.py**
  - AI prompt generation for sentence creation
  - Parameter combinations and prompt structure

### Problems Domain
- **tests/problems/test_problems_schemas.py**
  - ProblemCreate, ProblemUpdate schema validation
  - Enum handling (ProblemType, Difficulty)
  
- **tests/problems/test_problem_repository.py**
  - CRUD operations
  - Filtering and search functionality
  
- **tests/problems/test_problem_service.py**
  - Business logic validation
  
- **tests/problems/test_problems_api.py**
  - HTTP endpoint testing

### CLI Domain
- **tests/cli/test_problems.py**
  - CLI command testing for problem management
  
- **tests/cli/test_sentences.py**
  - CLI command testing for sentence management

### Main Application
- **tests/test_main.py**
  - FastAPI application startup and configuration
  
- **tests/test_security.py**
  - Authentication and authorization testing

## Directory of Test Fixtures

### Global Fixtures (tests/conftest.py)

#### Database Fixtures
- `postgres_container`: PostgreSQL testcontainer instance  
- `test_database_url`: Database connection URL for test container
- `test_asyncpg_connection`: Direct asyncpg connection to test database
- `initialized_test_database`: Database with schema and essential data loaded

#### Schema Fixtures
- `sample_sentence_create`: SentenceCreate schema instance for testing
- `sample_sentence_with_custom_data`: SentenceCreate with specific test data

### Domain-Specific Fixtures and Helpers

#### Verbs Domain (tests/verbs/)
- **fixtures.py**: Data generation functions
  - `generate_random_verb_data()`: Generate random verb data for testing
  - `generate_random_conjugation_data()`: Generate random conjugation data
  - Pre-defined known verb and conjugation data for predictable testing
  
- **db_helpers.py**: Database operation helpers
  - `create_verb()`, `get_verb()`, `update_verb()`, `delete_verb()`
  - `create_conjugation()`, `get_conjugation()`, `upsert_conjugation()`
  - `search_verbs()`, `get_random_verb()`, `count_verbs()`
  - `clear_verb_domain()` for test cleanup

#### Sentences Domain (tests/sentences/)
- **fixtures.py**: Data generation functions
  - `generate_random_sentence_data()`: Generate random sentence data
  - `generate_random_sentence_data_with_verb()`: Generate data with verb relationship
  
- **db_helpers.py**: Database operation helpers  
  - `create_sentence()`, `get_sentence()`, `update_sentence()`, `delete_sentence()`
  - `get_sentences_by_verb()`, `get_random_sentence()`, `search_sentences()`
  - `get_sentences_with_complex_filters()` for advanced filtering
  - `create_test_sentences_batch()` for bulk testing
  - `clear_sentences()` for test cleanup

#### Problems Domain (tests/problems/)
- **db_helpers.py**: Database operation helpers
  - `create_problem()`, `get_problem()`, `update_problem()`, `delete_problem()`
  - `get_problems()`, `count_problems()`, `search_problems()`  
  - `clear_problems()` for test cleanup

### Fixture Design Philosophy

1. **Separation of Concerns**: Data generation (fixtures.py) separated from database operations (db_helpers.py)
2. **Domain Objects**: All helpers work with Pydantic domain objects, not raw dictionaries
3. **High-Level Abstractions**: Helpers provide business-meaningful operations
4. **Type Safety**: Full type hints and automatic JSON/UUID handling
5. **Test Isolation**: Clear cleanup functions ensure test independence

## Test Configuration

### Pytest Configuration (pyproject.toml)
- **Markers**: `unit`, `integration`, `api`, `cli`
- **Coverage**: 80% minimum threshold
- **Async Support**: pytest-asyncio for async test functions
- **Faker Integration**: pytest-faker for data generation

### Test Environment
- **Database**: PostgreSQL via testcontainers
- **Isolation**: Each test gets fresh database state
- **Parallelization**: Tests can run in parallel with proper isolation
- **CI/CD**: Configured for GitHub Actions

## Running Tests

### Full Test Suite
```bash
python -m pytest
```

### Domain-Specific Tests
```bash
python -m pytest tests/sentences/
python -m pytest tests/verbs/
python -m pytest tests/problems/
```

### Test Type Filters
```bash
python -m pytest -m unit          # Unit tests only
python -m pytest -m integration   # Integration tests only
python -m pytest -m api          # API tests only
```

### Coverage Reports
```bash
python -m pytest --cov=src --cov-report=html
```

## Migration Guide

### From Mock-Based to Direct Database Tests

Our architecture has evolved from MockSupabaseClient to direct database calls for better performance and reliability:

1. **Repository Test Pattern**:
   ```python
   # New approach - Direct database with db_helpers
   async def test_create_verb(test_asyncpg_connection):
       # Use db helpers for setup
       verb_data = generate_random_verb_data()
       verb = await create_verb(test_asyncpg_connection, verb_data)
       
       # Test repository with direct connection
       repository = VerbRepository(connection=test_asyncpg_connection)
       result = await repository.get_verb(verb.id)
       
       assert result.infinitive == verb_data["infinitive"]
   ```

2. **Use Domain Object Helpers**: Replace raw SQL with domain-specific helper functions
3. **Constraint Testing**: Use helper methods with invalid data instead of raw SQL
4. **Test Isolation**: Use clear_* functions for domain cleanup between tests

### Key Architecture Changes

- **No More MockSupabaseClient**: Direct asyncpg connections replace complex API mocking
- **DB Helpers**: Domain-specific helpers replace low-level database operations  
- **Fixtures vs Helpers**: Data generation (fixtures.py) separated from database operations (db_helpers.py)
- **Type Safety**: Full Pydantic integration with automatic type conversions

### Best Practices

1. **Test Data**: Use generate_* functions from fixtures.py for consistent data
2. **Database Operations**: Use db_helpers.py functions for all database interactions
3. **Isolation**: Clear domain data between tests using clear_* functions
4. **Constraints**: Test database constraints using domain objects, not raw SQL
5. **Performance**: Direct database calls are faster than API translation layers

## Troubleshooting

### Common Issues

1. **Foreign Key Violations**: Use helper functions to create related entities first
2. **Type Conversions**: DB helpers handle JSON/UUID conversions automatically  
3. **Async Test Issues**: Ensure proper `@pytest.mark.asyncio` decoration
4. **Container Startup**: Check Docker availability for testcontainers

### Debug Tips

1. **Verbose Output**: Use `-v` flag for detailed test output
2. **Database Inspection**: Use `test_asyncpg_connection` fixture for direct queries
3. **Fixture Debugging**: Print fixture values to understand test state
4. **Coverage Analysis**: Use coverage reports to identify untested code paths 