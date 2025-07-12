# Language Quiz Service Testing Strategy

## Overview

This document outlines the comprehensive testing strategy for the language-quiz-service project, designed to provide robust test coverage while maintaining clarity and maintainability. The strategy is modeled after the successful language-service-backend testing approach.

## Testing Philosophy

### Four-Tier Testing Approach

| Test Type | Scope | Dependencies | Purpose | Execution Speed |
|-----------|-------|--------------|---------|-----------------|
| **Unit** | Single function/method | Mocked | Fast feedback, code coverage | < 1s per test |
| **Integration** | Component interactions | All mocked | Contract validation | < 1s per test |
| **Functional** | Complete features | Real APIs (no external services) | End-to-end workflows | < 1s per test |
| **Acceptance** | User scenarios | Real services (no LLMs) | Production readiness | 10-20s per run (parallel) |

### Pytest Markers

All tests must be marked with appropriate pytest markers:

```python
@pytest.mark.unit          # Fast, isolated, mocked dependencies
@pytest.mark.integration   # Component interaction tests
@pytest.mark.functional    # Feature-complete tests
@pytest.mark.acceptance    # Production-safe, read-only tests
```

## Directory Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── pytest.ini                    # Pytest configuration
├── 
├── # === CONCERN-BASED ORGANIZATION ===
├── test_verbs_schemas.py          # Unit tests for verb Pydantic models
├── test_verbs_repository.py       # Unit tests for verb data access
├── test_verbs_service.py          # Unit tests for verb business logic
├── test_verbs_api.py              # Integration tests for verb endpoints (future)
├── 
├── test_sentences_schemas.py      # Unit tests for sentence models
├── test_sentences_repository.py   # Unit tests for sentence data access
├── test_sentences_service.py      # Unit tests for sentence business logic
├── test_sentences_api.py          # Integration tests for sentence endpoints (future)
├── 
├── test_problems_schemas.py       # Unit tests for problem models
├── test_problems_repository.py    # Unit tests for problem data access
├── test_problems_service.py       # Unit tests for problem business logic
├── test_problems_api.py           # Integration tests for problem endpoints (future)
├── 
├── # === CROSS-CUTTING CONCERNS ===
├── test_clients.py               # Unit tests for external clients
├── test_database.py              # Integration tests for database operations
├── test_config.py                # Unit tests for configuration
├── test_utils.py                 # Unit tests for utility functions
├── 
├── # === FUTURE API TESTING ===
├── test_main.py                  # Integration tests for FastAPI app (future)
└── test_monitoring.py           # Tests for health checks and metrics (future)
```

## Testing Patterns by Layer

### 1. Schema Testing (`test_*_schemas.py`)

**Purpose**: Validate Pydantic models, serialization, and validation logic.

**Pattern**:
```python
@pytest.mark.unit
class TestVerbCreate:
    def test_valid_verb_creation(self):
        """Test creating valid verb with all required fields."""
        
    def test_verb_validation_failures(self):
        """Test various validation failures."""
        
    def test_field_normalization(self):
        """Test automatic field normalization (trim, lowercase)."""

@pytest.mark.unit  
class TestVerbUpdate:
    def test_partial_updates(self):
        """Test partial update scenarios."""

@pytest.mark.unit
class TestVerbEnum:
    def test_auxiliary_type_values(self):
        """Test enum value validation."""
```

**Key Testing Areas**:
- Valid model creation with all required fields
- Validation failures for invalid data
- Field normalization (trim whitespace, case conversion)
- Enum value validation
- Optional vs required field handling
- JSON serialization/deserialization
- Model inheritance and composition

### 2. Repository Testing (`test_*_repository.py`)

**Purpose**: Test data access layer with mocked Supabase client.

**Pattern**:
```python
@pytest.mark.unit
class TestVerbRepository:
    def test_create_verb_success(self, mock_supabase_client):
        """Test successful verb creation."""
        
    def test_create_verb_database_error(self, mock_supabase_client):
        """Test handling of database errors."""
        
    def test_get_verb_by_id_found(self, mock_supabase_client):
        """Test retrieving existing verb."""
        
    def test_get_verb_by_id_not_found(self, mock_supabase_client):
        """Test handling of missing verb."""

@pytest.mark.integration
class TestVerbRepositoryIntegration:
    def test_full_crud_cycle(self, real_supabase_client):
        """Test complete CRUD operations against real database."""
```

**Key Testing Areas**:
- CRUD operations (Create, Read, Update, Delete)
- Query filtering and search functionality
- Error handling for database failures
- UUID handling and conversion
- Pagination and limiting
- Complex queries with joins
- Transaction handling (when applicable)
- Connection error scenarios

### 3. Service Testing (`test_*_service.py`)

**Purpose**: Test business logic with mocked dependencies.

**Pattern**:
```python
@pytest.mark.unit
class TestVerbService:
    def test_create_verb_valid_data(self, mock_verb_repository):
        """Test verb creation with valid data."""
        
    def test_create_verb_duplicate_handling(self, mock_verb_repository):
        """Test handling of duplicate verbs."""
        
    def test_download_verb_ai_integration(self, mock_openai_client, mock_verb_repository):
        """Test AI-powered verb downloading."""

@pytest.mark.integration
class TestVerbServiceIntegration:
    def test_ai_verb_processing_end_to_end(self, real_ai_client, mock_repository):
        """Test complete AI integration workflow."""
```

**Key Testing Areas**:
- Business logic validation
- Dependency coordination (repository, AI clients)
- Error handling and recovery
- Data transformation and mapping
- AI integration and response processing
- Caching and optimization logic
- Validation of business rules
- Performance considerations

### 4. API Testing (`test_*_api.py`) - Future

**Purpose**: Test HTTP endpoints and API contracts.

**Pattern**:
```python
@pytest.mark.integration
class TestVerbAPI:
    def test_create_verb_endpoint(self, test_client):
        """Test POST /verbs endpoint."""
        
    def test_get_verb_endpoint(self, test_client):
        """Test GET /verbs/{id} endpoint."""

@pytest.mark.functional
class TestVerbWorkflows:
    def test_complete_verb_learning_workflow(self, test_client):
        """Test end-to-end verb learning scenario."""
```

## Fixture Strategy

### Core Fixtures (`conftest.py`)

```python
# === MOCK FIXTURES ===
@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for unit tests."""

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for unit tests."""

@pytest.fixture  
def mock_verb_repository():
    """Mock verb repository for service tests."""

# === DATA FIXTURES ===
@pytest.fixture
def sample_verb_data():
    """Sample verb data for testing."""

@pytest.fixture
def sample_conjugation_data():
    """Sample conjugation data for testing."""

# === INTEGRATION FIXTURES ===
@pytest.fixture(scope="session")
def real_supabase_client():
    """Real Supabase client for integration tests."""

@pytest.fixture
def test_database():
    """Test database with cleanup."""
```

### Fixture Scope Strategy

- **Session**: Database connections, expensive setup
- **Module**: Shared test data within a test file
- **Function**: Isolated test instances (default)

## Parameterized Testing Strategy

### Use Parameterized Tests Extensively

Parameterized tests are **essential** for comprehensive testing while maintaining DRY principles:

```python
@pytest.mark.unit
@pytest.mark.parametrize("language_code,expected_valid", [
    ("fra", True),
    ("eng", True), 
    ("cmn", True),
    ("ab", False),   # Too short
    ("abcd", False), # Too long
    ("", False),     # Empty
    ("12a", False),  # Numbers
])
def test_language_code_validation(language_code, expected_valid):
    """Test language code validation with multiple inputs."""
    if expected_valid:
        # Should not raise
        verb = VerbCreate(source_language_code=language_code, ...)
        assert verb.source_language_code == language_code.lower()
    else:
        with pytest.raises(ValueError):
            VerbCreate(source_language_code=language_code, ...)

@pytest.mark.unit
@pytest.mark.parametrize("auxiliary,classification,is_irregular", [
    (AuxiliaryType.AVOIR, VerbClassification.FIRST_GROUP, False),
    (AuxiliaryType.ETRE, VerbClassification.THIRD_GROUP, True),
    (AuxiliaryType.AVOIR, VerbClassification.SECOND_GROUP, False),
])
def test_verb_combinations(auxiliary, classification, is_irregular):
    """Test various valid verb combinations."""
    verb = VerbCreate(
        auxiliary=auxiliary,
        classification=classification,
        is_irregular=is_irregular,
        # ... other required fields
    )
    assert verb.auxiliary == auxiliary
    assert verb.classification == classification
    assert verb.is_irregular == is_irregular
```

### When to Use Parameterized Tests

- **Validation testing**: Multiple valid/invalid inputs
- **Edge cases**: Boundary conditions and special cases  
- **Error scenarios**: Different types of failures
- **Data transformation**: Various input/output combinations
- **Cross-platform concerns**: Different configurations

### Parameterized Test Benefits

- **Comprehensive coverage** with minimal code duplication
- **Clear test failure isolation** - know exactly which case failed
- **Easy maintenance** - add new test cases by adding parameters
- **Better documentation** - parameters show all supported scenarios

## Test Data Management - CRITICAL RULES

### ⚠️ **NEVER Add Test Data to Service Code**

**ABSOLUTELY FORBIDDEN** without explicit approval:

```python
# ❌ NEVER DO THIS - Test data in service code
class VerbService:
    def get_sample_verbs(self):
        return [
            {"infinitive": "parler", "translation": "to speak"},  # NO!
            {"infinitive": "finir", "translation": "to finish"},   # NO!
        ]

# ❌ NEVER DO THIS - Fallback test data in production code  
def get_verb_or_fallback(verb_id):
    verb = repository.get_verb(verb_id)
    if not verb:
        return {"infinitive": "test", "translation": "test"}  # NO!
```

### ✅ **Correct Approach - Test Data in Tests Only**

```python
# ✅ Test data belongs in test fixtures
@pytest.fixture
def sample_verbs():
    """Sample verb data for testing only."""
    return [
        VerbCreate(infinitive="parler", translation="to speak", ...),
        VerbCreate(infinitive="finir", translation="to finish", ...),
    ]

# ✅ Test data in parameterized tests
@pytest.mark.parametrize("verb_data", [
    {"infinitive": "parler", "auxiliary": "avoir"},
    {"infinitive": "aller", "auxiliary": "être"},
])
def test_verb_creation(verb_data):
    """Test verb creation with sample data."""
```

### Why This Rule Exists

**Test data in service code causes**:
- **Production bugs** when test data leaks into real workflows
- **Data corruption** in production databases
- **Security issues** with hardcoded credentials or tokens
- **Maintenance nightmares** when test scenarios change
- **Unclear separation** between test and production behavior

### **Before Adding ANY Test Data**

**You MUST**:
1. **Ask permission first** - explain why fixtures/mocks won't work
2. **Provide clear justification** - what production need does this serve?
3. **Show isolation strategy** - how will you prevent production leakage?
4. **Include removal plan** - when and how will this be cleaned up?

### Approved Alternatives

Instead of service-level test data:
- **Fixtures** for test-specific data
- **Mock responses** for external services  
- **Test databases** with known datasets
- **Factories** for generating test objects
- **Builders** for complex test scenarios

### Sample Data Fixtures

```python
@pytest.fixture
def sample_french_verb():
    """Sample French verb for testing."""
    return VerbCreate(
        infinitive="parler",
        auxiliary=AuxiliaryType.AVOIR,
        reflexive=False,
        source_language_code="fra",
        translation="to speak",
        past_participle="parlé",
        present_participle="parlant",
        classification=VerbClassification.FIRST_GROUP,
        is_irregular=False
    )

@pytest.fixture
def sample_irregular_verb():
    """Sample irregular verb for edge case testing."""
    return VerbCreate(
        infinitive="être",
        auxiliary=AuxiliaryType.ETRE,
        reflexive=False,
        source_language_code="fra", 
        translation="to be",
        past_participle="été",
        present_participle="étant",
        classification=VerbClassification.THIRD_GROUP,
        is_irregular=True
    )
```

## Mock Strategy

### Repository Mocking

```python
@pytest.fixture
def mock_verb_repository():
    """Mock verb repository with common behaviors."""
    mock = Mock(spec=VerbRepository)
    mock.create_verb = AsyncMock()
    mock.get_verb = AsyncMock()
    mock.update_verb = AsyncMock()
    mock.delete_verb = AsyncMock()
    return mock
```

### External Client Mocking

```python
@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for AI integration tests."""
    mock = Mock()
    mock.handle_request = AsyncMock()
    return mock
```

## Configuration

### pytest.ini

```ini
[tool:pytest]
markers =
    unit: Unit tests with mocked dependencies
    integration: Integration tests between components  
    functional: End-to-end feature tests
    acceptance: Read-only tests safe for production
    slow: Tests that take longer to run

testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Coverage settings
addopts = 
    --strict-markers
    --strict-config
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80

# Async test support
asyncio_mode = auto

# Filter warnings
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

## Test Execution Strategy

### Local Development

```bash
# Run all unit tests (fast feedback)
pytest -m unit

# Run tests for specific concern
pytest tests/test_verbs_*.py

# Run with coverage
pytest --cov=src/services/verb_service tests/test_verbs_service.py

# Run specific test class
pytest tests/test_verbs_repository.py::TestVerbRepository::test_create_verb
```

### CI/CD Pipeline

```bash
# Parallel execution by marker
pytest -m unit --maxfail=5
pytest -m integration --maxfail=3  
pytest -m functional --maxfail=1

# Full test suite with coverage
pytest --cov=src --cov-fail-under=80
```

## Error Handling Testing

### Exception Testing Patterns

```python
@pytest.mark.unit
def test_invalid_language_code_raises_error():
    """Test that invalid language codes raise appropriate errors."""
    with pytest.raises(ValueError, match="Language code must be"):
        VerbCreate(source_language_code="invalid")

@pytest.mark.unit  
def test_repository_error_handling(mock_supabase_client):
    """Test service handles repository errors gracefully."""
    mock_supabase_client.table.return_value.insert.side_effect = Exception("DB Error")
    
    with pytest.raises(Exception):
        # Test error propagation
        pass
```

## Migration Strategy

### Phase 1: Clean Slate Setup
1. **Remove existing tests**: Clear current `tests/` directory
2. **Setup structure**: Create new directory structure
3. **Core fixtures**: Implement `conftest.py` with essential fixtures
4. **Basic configuration**: Setup `pytest.ini` and markers

### Phase 2: Verb Stack Implementation  
1. **Schema tests**: Implement `test_verbs_schemas.py`
2. **Repository tests**: Implement `test_verbs_repository.py` 
3. **Service tests**: Implement `test_verbs_service.py`
4. **Integration tests**: Add integration test cases

### Phase 3: Expansion (Future)
1. **Additional concerns**: Sentences, problems, etc.
2. **API integration**: When FastAPI endpoints are added
3. **Security tests**: Authentication and authorization
4. **Performance tests**: Load and stress testing

## Quality Gates

### Coverage Requirements
- **Unit tests**: 90%+ coverage for individual components
- **Integration tests**: Key user workflows covered
- **Overall**: 80%+ combined coverage with 100% pass rate

### Test Quality Metrics
- **Test execution time**: Unit tests < 10 minutes total
- **Test reliability**: 100% pass rate required - failing tests block development

## Best Practices

### Test Naming Conventions
- Test files: `test_{concern}_{layer}.py`
- Test classes: `Test{ComponentName}`
- Test methods: `test_{what}_{scenario}` (e.g., `test_create_verb_with_valid_data`)

### Test Organization
- **Group related tests in classes** for logical organization
- **Use descriptive docstrings** explaining what the test validates
- **Keep tests focused and atomic** - one concept per test
- **Use parameterized tests extensively** - avoid duplicating test logic
- **Prefer factories over hardcoded data** for complex test objects

### Assertion Strategy
- Use specific assertions with clear error messages
- Test both positive and negative cases  
- Verify state changes, not just return values
- Include edge cases and boundary conditions

### Parameterized Testing Best Practices
- **Always use `@pytest.mark.parametrize`** for multiple similar test cases
- **Name parameters clearly** - use descriptive parameter names
- **Include edge cases** in parameter lists (empty, null, boundary values)
- **Add inline comments** for complex parameter combinations
- **Group related parameters** using tuples or dictionaries

### Test Data Rules (CRITICAL)
- **NEVER put test data in service/production code** without explicit approval
- **Use fixtures for test data** - keep it in the test layer
- **Mock external dependencies** rather than using real test accounts
- **Clean up test data** after test execution
- **Ask before adding any fallback data** to production code

This testing strategy provides a solid foundation for maintaining code quality while supporting rapid development and refactoring of the language-quiz-service codebase.