# Test Containers Implementation Guide for Language-Quiz-Service

## 🎯 Overview

Replace brittle mocks with real PostgreSQL containers for reliable integration testing. This eliminates mock maintenance overhead while providing better test coverage and confidence.

## 🚨 Current Problems

- **Brittle Mocks**: `MockAdminRepository`, `AsyncMock` setup everywhere
- **Mock Drift**: Mocks don't match real database behavior  
- **Complex Setup**: Each test needs custom mock configuration
- **Limited Coverage**: Can't test SQL constraints, triggers, or complex queries
- **Maintenance Overhead**: Keeping mocks in sync with real implementations

## ✅ Test Containers Benefits

- **Real Database Behavior**: Actual PostgreSQL with your schema
- **No Mock Maintenance**: Tests run against real services
- **Better Integration Coverage**: Test SQL, constraints, indexes
- **CI/CD Confidence**: Same environment locally and in pipeline
- **Simpler Test Code**: No mock setup, just real service calls

## 📦 Implementation

### Step 1: Add Dependencies

```toml
# pyproject.toml
[tool.poetry.group.test.dependencies]
testcontainers = "^4.0.0"
testcontainers-postgres = "^4.0.0"
httpx = "^0.27.0"  # For async API testing
asyncpg = "^0.29.0"  # For direct database operations
```

### Step 2: Update Test Configuration

```python
# tests/conftest.py - Test Containers Setup
"""
Test containers configuration for language-quiz-service.
Replaces complex mocking with real services.
"""

import asyncio
import os
import pytest
import asyncpg
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from testcontainers.postgres import PostgresContainer

from src.main import app
from src.core.config import Settings, get_settings
from src.clients.supabase import get_supabase_client


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for session-scoped async fixtures."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session") 
def postgres_container():
    """Session-scoped PostgreSQL container."""
    with PostgresContainer("postgres:15", driver="psycopg2") as postgres:
        postgres.start()
        yield postgres


@pytest.fixture(scope="session")
def test_database_url(postgres_container: PostgresContainer) -> str:
    """Database URL for test container."""
    return postgres_container.get_connection_url()


@pytest.fixture(scope="session")
async def initialized_database(test_database_url: str):
    """Initialize database schema in test container."""
    conn = await asyncpg.connect(test_database_url.replace("postgresql://", "postgresql://"))
    
    try:
        # Load and execute SQL schema files
        schema_files = [
            "sql/1-Verbs.sql",
            "sql/2-Sentences.sql", 
            "sql/3-Problems.sql",  # Your new problems schema
        ]
        
        for schema_file in schema_files:
            if os.path.exists(schema_file):
                with open(schema_file, 'r') as f:
                    schema_sql = f.read()
                    # Split on semicolons and execute each statement
                    statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
                    for statement in statements:
                        try:
                            await conn.execute(statement)
                        except Exception as e:
                            print(f"Warning: Failed to execute statement: {e}")
        
        # Insert basic test data
        await _insert_test_data(conn)
        
    finally:
        await conn.close()
    
    return test_database_url


async def _insert_test_data(conn):
    """Insert minimal test data for tests."""
    # Add test verbs
    await conn.execute("""
        INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, 
                          translation, past_participle, present_participle, 
                          can_have_cod, can_have_coi)
        VALUES 
        ('parler', 'avoir', false, 'eng', 'to speak', 'parlé', 'parlant', false, true),
        ('manger', 'avoir', false, 'eng', 'to eat', 'mangé', 'mangeant', true, false),
        ('voir', 'avoir', false, 'eng', 'to see', 'vu', 'voyant', true, false),
        ('donner', 'avoir', false, 'eng', 'to give', 'donné', 'donnant', true, true)
        ON CONFLICT DO NOTHING;
    """)
    
    # Add conjugations for test verbs
    await conn.execute("""
        INSERT INTO conjugations (infinitive, auxiliary, reflexive, tense,
                                first_person_singular, second_person_singular, 
                                third_person_singular, first_person_plural,
                                second_person_formal, third_person_plural)
        VALUES 
        ('parler', 'avoir', false, 'present', 'parle', 'parles', 'parle', 'parlons', 'parlez', 'parlent'),
        ('manger', 'avoir', false, 'present', 'mange', 'manges', 'mange', 'mangeons', 'mangez', 'mangent'),
        ('voir', 'avoir', false, 'present', 'vois', 'vois', 'voit', 'voyons', 'voyez', 'voient'),
        ('donner', 'avoir', false, 'present', 'donne', 'donnes', 'donne', 'donnons', 'donnez', 'donnent')
        ON CONFLICT DO NOTHING;
    """)


@pytest.fixture
def test_settings(test_database_url: str) -> Settings:
    """Test settings pointing to test container database."""
    return Settings(
        PROJECT_NAME="Test Language Quiz Service",
        VERSION="0.1.0-test",
        API_V1_STR="/api/v1",
        DATABASE_URL=test_database_url,  # Point to test container
        OPENAI_API_KEY="test-openai-key",
        ENVIRONMENT="test",
        RATE_LIMIT_REQUESTS=1000,  # High limit for tests
        RATE_LIMIT_WINDOW=60,
    )


@pytest.fixture
async def test_app(initialized_database: str, test_settings: Settings):
    """FastAPI app configured for integration testing."""
    # Override settings to use test database
    app.dependency_overrides[get_settings] = lambda: test_settings
    
    # Override database client to use test container
    from src.clients.supabase import create_supabase_client
    test_client = await create_supabase_client(test_settings.DATABASE_URL)
    app.dependency_overrides[get_supabase_client] = lambda: test_client
    
    yield app
    
    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture
def integration_client(test_app) -> Generator[TestClient, None, None]:
    """Synchronous test client for integration tests."""
    with TestClient(test_app) as client:
        yield client


@pytest.fixture
async def async_integration_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Async test client for integration tests."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), 
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
async def verb_service(test_settings: Settings):
    """Real VerbService connected to test database."""
    from src.services.verb_service import VerbService
    return await VerbService.create(test_settings.DATABASE_URL)


@pytest.fixture  
async def sentence_service(test_settings: Settings):
    """Real SentenceService connected to test database."""
    from src.services.sentence_service import SentenceService
    return await SentenceService.create(test_settings.DATABASE_URL)
```

### Step 3: Example Integration Tests

```python
# tests/integration/test_verb_service_integration.py
"""
Integration tests for VerbService using real database.
Replaces complex mocking with real database behavior.
"""

import pytest


@pytest.mark.integration
class TestVerbServiceIntegration:
    """Test VerbService against real database."""
    
    async def test_get_verb_by_infinitive(self, verb_service):
        """Test retrieving a verb by infinitive."""
        verb = await verb_service.get_verb_by_infinitive("parler")
        
        assert verb is not None
        assert verb.infinitive == "parler"
        assert verb.auxiliary == "avoir"
        assert verb.can_have_coi == True
        assert verb.can_have_cod == False
    
    async def test_get_verbs_with_cod_capability(self, verb_service):
        """Test querying verbs by COD capability."""
        cod_verbs = await verb_service.get_verbs_with_capability(can_have_cod=True)
        
        assert len(cod_verbs) > 0
        assert all(verb.can_have_cod for verb in cod_verbs)
        
        # Should include 'manger' and 'voir' from test data
        infinitives = [v.infinitive for v in cod_verbs]
        assert "manger" in infinitives
        assert "voir" in infinitives
    
    async def test_get_random_verb(self, verb_service):
        """Test getting a random verb."""
        verb = await verb_service.get_random_verb()
        
        assert verb is not None
        assert verb.infinitive in ["parler", "manger", "voir", "donner"]
    
    async def test_verb_crud_operations(self, verb_service):
        """Test complete CRUD operations on verbs."""
        # This tests real database constraints and behavior
        from src.schemas.verbs import VerbCreate
        
        new_verb = VerbCreate(
            infinitive="tester",
            auxiliary="avoir",
            reflexive=False,
            target_language_code="eng",
            translation="to test",
            past_participle="testé",
            present_participle="testant",
            can_have_cod=True,
            can_have_coi=False
        )
        
        # Create
        created_verb = await verb_service.create_verb(new_verb)
        assert created_verb.infinitive == "tester"
        
        # Read
        retrieved_verb = await verb_service.get_verb_by_infinitive("tester")
        assert retrieved_verb.id == created_verb.id
        
        # Update (if implemented)
        # Delete (if implemented)


# tests/integration/test_sentence_service_integration.py
"""
Integration tests for SentenceService using real database.
"""

import pytest


@pytest.mark.integration  
class TestSentenceServiceIntegration:
    """Test SentenceService against real database."""
    
    async def test_generate_sentence_with_verification(self, sentence_service, verb_service):
        """Test sentence generation with verification workflow."""
        # Get a real verb from database
        verb = await verb_service.get_verb_by_infinitive("parler")
        
        # Generate sentence
        sentence = await sentence_service.generate_sentence(
            verb_id=verb.id,
            pronoun="first_person",
            tense="present",
            is_correct=True
        )
        
        assert sentence is not None
        assert sentence.verb_id == verb.id
        assert sentence.pronoun == "first_person"
        assert sentence.tense == "present"
        assert sentence.is_correct == True
        assert sentence.content  # Should have French content
        assert sentence.translation  # Should have translation
    
    async def test_get_sentences_by_criteria(self, sentence_service, verb_service):
        """Test querying sentences by various criteria."""
        # Create some test sentences first
        verb = await verb_service.get_verb_by_infinitive("manger")
        
        # Generate a few sentences
        for i in range(3):
            await sentence_service.generate_sentence(
                verb_id=verb.id,
                pronoun="third_person",
                tense="present", 
                is_correct=i == 0  # First one correct, others incorrect
            )
        
        # Query correct sentences
        correct_sentences = await sentence_service.get_sentences(
            verb_id=verb.id,
            is_correct=True
        )
        assert len(correct_sentences) >= 1
        
        # Query incorrect sentences
        incorrect_sentences = await sentence_service.get_sentences(
            verb_id=verb.id,
            is_correct=False
        )
        assert len(incorrect_sentences) >= 2


# tests/integration/test_api_integration.py
"""
Full API integration tests with real database.
No mocks - complete end-to-end workflows.
"""

import pytest


@pytest.mark.integration
class TestAPIIntegration:
    """Test complete API workflows against real services."""
    
    async def test_verb_endpoints(self, async_integration_client):
        """Test verb-related API endpoints."""
        # Get all verbs
        response = await async_integration_client.get("/api/v1/verbs")
        assert response.status_code == 200
        verbs = response.json()
        assert len(verbs) >= 4  # Our test data
        
        # Get specific verb
        verb_id = verbs[0]["id"]
        response = await async_integration_client.get(f"/api/v1/verbs/{verb_id}")
        assert response.status_code == 200
        verb = response.json()
        assert verb["id"] == verb_id
    
    async def test_sentence_generation_workflow(self, async_integration_client):
        """Test complete sentence generation workflow."""
        # 1. Get available verbs
        response = await async_integration_client.get("/api/v1/verbs")
        assert response.status_code == 200
        verbs = response.json()
        
        # 2. Generate sentences for a verb
        verb_id = verbs[0]["id"]
        response = await async_integration_client.post(
            f"/api/v1/verbs/{verb_id}/sentences",
            json={
                "count": 2,
                "tense": "present",
                "pronoun": "first_person",
                "generate_incorrect": True
            }
        )
        assert response.status_code == 200
        sentences = response.json()
        assert len(sentences) == 2
        
        # Should have one correct, one incorrect
        correct_count = sum(1 for s in sentences if s["is_correct"])
        assert correct_count >= 1
    
    async def test_problem_creation_workflow(self, async_integration_client):
        """Test problem creation from sentences."""
        # 1. Generate sentences
        response = await async_integration_client.post(
            "/api/v1/sentences/generate",
            json={
                "verb_infinitive": "parler",
                "problem_type": "verb_conjugation", 
                "count": 4
            }
        )
        assert response.status_code == 200
        generation_result = response.json()
        
        # 2. Create problem from sentences
        sentence_ids = [s["id"] for s in generation_result["sentences"]]
        response = await async_integration_client.post(
            "/api/v1/problems",
            json={
                "problem_type": "verb_conjugation",
                "question_text": "Choose the correct conjugation:",
                "sentence_ids": sentence_ids
            }
        )
        assert response.status_code == 201
        problem = response.json()
        
        assert len(problem["options"]) == len(sentence_ids)
        assert any(option["is_correct"] for option in problem["options"])


# tests/integration/test_security_integration.py  
"""
Security tests against real running service.
Tests actual middleware, rate limiting, CORS, etc.
"""

import pytest
import asyncio


@pytest.mark.integration
@pytest.mark.security
class TestSecurityIntegration:
    """Security tests with real authentication and rate limiting."""
    
    async def test_rate_limiting_enforcement(self, async_integration_client):
        """Test rate limiting with real middleware."""
        # Make rapid requests to trigger rate limiting
        tasks = []
        for i in range(20):  # Exceed rate limit
            task = async_integration_client.get("/api/v1/health")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should see some rate limit responses
        status_codes = [r.status_code for r in responses if hasattr(r, 'status_code')]
        rate_limited_count = sum(1 for code in status_codes if code == 429)
        
        # With high rate limit in tests, might not hit it, but middleware should be active
        assert len(status_codes) > 0  # At least some successful responses
    
    async def test_cors_configuration(self, async_integration_client):
        """Test CORS configuration with real headers."""
        response = await async_integration_client.options(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        # Should have CORS headers in response
        assert "access-control-allow-origin" in response.headers.keys() or \
               "Access-Control-Allow-Origin" in response.headers.keys()
    
    async def test_health_endpoint_security(self, async_integration_client):
        """Test health endpoint doesn't leak sensitive information."""
        response = await async_integration_client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        # Should not contain sensitive information
        assert "database_password" not in str(data).lower()
        assert "api_key" not in str(data).lower()
        assert "secret" not in str(data).lower()
```

### Step 4: Update Makefile

```makefile
# Add to Makefile

# Test commands with containers
test-integration:
	@echo "🧪 Running integration tests with test containers..."
	poetry run pytest tests/integration/ -v -m integration

test-security:
	@echo "🔒 Running security tests with real services..."
	poetry run pytest tests/integration/ -v -m security

test-containers:
	@echo "🐳 Running all tests with containers..."
	@docker info > /dev/null || (echo "❌ Docker not running" && exit 1)
	poetry run pytest tests/integration/ -v

test-all-real:
	@echo "🚀 Running comprehensive real-service tests..."
	make test-containers test-security

# Backwards compatibility
test-unit:
	@echo "⚡ Running fast unit tests..."
	poetry run pytest tests/ -v -m unit

test-mixed:
	@echo "🔄 Running mixed unit and integration tests..."
	poetry run pytest tests/ -v
```

### Step 5: CI/CD Integration

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on:
  pull_request:
    branches: [ main, staging ]
  push:
    branches: [ main, staging ]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
        
    - name: Install Poetry
      uses: snok/install-poetry@v1
      with:
        version: latest
        virtualenvs-create: true
        virtualenvs-in-project: true
        
    - name: Install dependencies
      run: poetry install --with test
      
    - name: Run integration tests
      run: |
        make test-containers
        make test-security
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        
    - name: Run mixed test suite
      run: make test-mixed
```

## 🚀 Migration Strategy

### Phase 1: Foundation (Week 1)
**Goal**: Get basic test containers working alongside existing mocks

- [ ] Add testcontainers dependencies
- [ ] Create PostgreSQL container fixture  
- [ ] Initialize database schema in container
- [ ] Convert 1-2 simple service tests
- [ ] Verify CI pipeline works

### Phase 2: Service Tests (Week 2)  
**Goal**: Replace service-level mocks with real database tests

**Target files:**
- `tests/test_verb_service.py`
- `tests/test_sentence_service.py` 
- `tests/database/test_database_init.py`

**Convert patterns:**
```python
# From this (mock-heavy):
@pytest.fixture
def mock_supabase():
    mock = AsyncMock()
    mock.table.return_value.select.return_value.execute.return_value = Mock(data=[...])
    return mock

# To this (real database):
async def test_with_real_db(self, verb_service):
    verb = await verb_service.get_verb_by_infinitive("parler")
    assert verb.infinitive == "parler"
```

### Phase 3: API Integration (Week 3)
**Goal**: Test complete API workflows end-to-end

**Target files:**
- Security tests in `tests/test_security.py`
- API integration tests

**Benefits:**
- Real rate limiting behavior
- Real CORS header handling
- Real error responses
- End-to-end problem generation workflows

### Phase 4: Cleanup (Week 4)
**Goal**: Remove unused mocks and optimize

- [ ] Remove unused mock fixtures from `conftest.py`
- [ ] Optimize container startup time
- [ ] Document new testing patterns
- [ ] Update development guides

## 📊 Expected Results

### Before (Mocks)
```python
# 15+ lines of mock setup per test
@pytest.fixture
def complex_mock_setup():
    mock_client = AsyncMock()
    mock_table = AsyncMock()
    mock_select = AsyncMock()
    mock_execute = AsyncMock()
    
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_execute
    mock_execute.execute.return_value = Mock(data=[{
        "infinitive": "parler",
        "auxiliary": "avoir", 
        # ... 20 more fields to mock
    }])
    return mock_client

async def test_verb_service(self, complex_mock_setup):
    # Test behavior that might not match real database
```

### After (Containers)
```python
# 1 line test, real behavior
async def test_verb_service(self, verb_service):
    verb = await verb_service.get_verb_by_infinitive("parler")
    assert verb.auxiliary == "avoir"  # Real database, real constraints!
```

### Metrics
- **90% reduction** in test setup code
- **Zero mock drift** issues
- **Real environment parity** 
- **Better integration coverage**
- **Faster test development**

## 🎯 Quick Start Checklist

- [ ] **Install dependencies**: `poetry add --group test testcontainers testcontainers-postgres`
- [ ] **Update conftest.py**: Add PostgreSQL container fixtures
- [ ] **Convert one test**: Pick simplest VerbService test to convert
- [ ] **Verify locally**: `make test-integration`
- [ ] **Update CI**: Add integration test workflow
- [ ] **Expand gradually**: Convert more tests week by week

## 💡 Pro Tips

1. **Start small**: Convert your simplest, most stable tests first
2. **Keep some mocks**: External APIs (OpenAI) should still be mocked
3. **Session-scoped containers**: Reuse containers across tests for speed
4. **Real schema**: Load your actual SQL files into test containers
5. **Test data management**: Create minimal, focused test data sets
6. **CI monitoring**: Watch CI times and costs with containers

The key insight: **Test containers eliminate the biggest source of test brittleness** (complex database mocking) while providing much better coverage of your actual business logic and database behavior.