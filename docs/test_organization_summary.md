# Test Organization Overhaul - Language-Quiz-Service

## ✅ Current State & Best Practices (2024)

- **Test files are organized by concern** (e.g., `tests/verbs/`, `tests/sentences/`, etc.), mirroring the `src/` structure.
- **Mocks and fixtures are local** to each test file or concern. Only simple, stable, pure-data fixtures (e.g., sample data) remain in `conftest.py`.
- **No complex or async mocks in `conftest.py`.** All repository/client/service mocks are defined per-file or per-concern.
- **All test classes are marked** with `@pytest.mark.unit` (or `@pytest.mark.integration` if needed in the future).
- **Test files can be further split by sub-concern** (e.g., by mock dependency) as the suite grows.
- **Contributors and AI agents:** When adding new tests, create local mocks/fixtures as needed, and keep sharing within the same concern only. Use markers and follow the directory structure.

---

## �� Current Problems

Your test suite is heading toward the same brittleness issues as language-level-backend, but you can fix them now while the codebase is still manageable:

### The Shared Mock Problem
- `tests/conftest.py` contains `MockAdminRepository()` used by all tests
- Single mock must serve every test case, creating brittleness
- Changes to satisfy one test break others
- AI agents spend more time fixing tests than writing features

### Async Event Loop Issues
- Session-scoped `event_loop` fixture can cause cross-test interference
- Shared fixtures create unpredictable test dependencies

## 🎯 Immediate Fixes (1 Hour Implementation)

### 1. Remove Shared Mocks from conftest.py (30 min)

**Before:**
```python
@pytest.fixture
def test_client(test_settings: Settings) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_admin_repository] = lambda: MockAdminRepository()
    # This shared mock serves ALL tests - brittle!
```

**After:**
```python
@pytest.fixture
def basic_test_client(test_settings: Settings) -> Generator[TestClient, None, None]:
    """Basic client WITHOUT dependency overrides."""
    app.dependency_overrides[get_settings] = lambda: test_settings
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
```

### 2. Create Local Mocks (15 min)

**Pattern for tests that need admin functionality:**
```python
@pytest.fixture
def admin_test_client(test_settings):
    """Local mock just for admin tests in this file."""
    mock = AsyncMock()
    mock.get_all_providers.return_value = [{"id": "1", "name": "test"}]
    
    app.dependency_overrides[get_admin_repository] = lambda: mock
    app.dependency_overrides[get_settings] = lambda: test_settings
    
    with TestClient(app) as client:
        yield client, mock
    app.dependency_overrides.clear()
```

### 3. Add Test Markers (10 min)

**pytest.ini:**
```ini
[tool:pytest]
markers =
    unit: Fast unit tests with no external dependencies
    integration: Integration tests with mocked services
    slow: Tests that take significant time
```

**Mark existing tests:**
```python
@pytest.mark.unit        # test_config.py, test_language_config.py
@pytest.mark.integration # test_admin_api.py, API endpoint tests
```

### 4. Update Makefile (5 min)

```makefile
test-unit:
	poetry run pytest -m "unit" -v

test-integration:
	poetry run pytest -m "integration" -v

test-fast:
	poetry run pytest -m "unit or (integration and not slow)" -v
```

## 📋 Implementation Checklist

### Week 1: Foundation (1 hour)
- [ ] Update `conftest.py` to remove `MockAdminRepository`
- [ ] Create `basic_test_client` fixture
- [ ] Add test markers to `pytest.ini`
- [ ] Mark existing tests with appropriate markers

### Week 2: Local Mocks (2 hours)
- [ ] Create local mock fixtures for admin tests
- [ ] Update tests that currently use shared `test_client`
- [ ] Create local mocks for translation tests
- [ ] Verify all tests still pass

### Week 3: Organization (1 hour)
- [ ] Group related tests into focused files
- [ ] Update Makefile for selective test execution
- [ ] Document new testing patterns

## 🎯 Expected Benefits

### For AI Agents
- **80% reduction** in test maintenance time
- **No more cascading test failures** from shared mock changes
- **Predictable test behavior** - each test is self-contained

### For Development
- **Fast feedback loops** with selective test execution
- **Scalable structure** that grows without complexity
- **Clear test boundaries** - easy to understand what each test does

### For CI/CD
- **Faster builds** with targeted test execution
- **Reliable tests** with reduced brittleness
- **Better failure isolation** - failures don't cascade

## 🔑 Key Principles Going Forward

### ✅ Do:
- Create local mocks in test files that use them
- Keep `conftest.py` for simple, stable fixtures only
- Use appropriate test markers
- Mock only what your specific test needs

### ❌ Don't:
- Add complex mocks to `conftest.py`
- Make one mock serve multiple unrelated test files
- Override app dependencies in global fixtures
- Create fixtures that try to handle every test case

## 🚀 Success Metrics

After implementation, you should see:
- [ ] Zero cross-test interference incidents
- [ ] Test execution time reduced by 50% for development
- [ ] AI agent test maintenance overhead reduced by 80%
- [ ] New tests don't break existing ones
- [ ] Clear separation between unit and integration tests

## 💡 Why This Matters Now

Your project is at the **perfect size** to fix this:
- **Small enough** that changes are quick (1-3 hours total)
- **Already showing signs** of the brittleness that becomes a nightmare later
- **Patterns you establish now** determine if your test suite becomes an accelerator or burden

The core insight: **Move from "one mock serves all tests" to "each test creates exactly what it needs"**. This eliminates the cascading failures that waste AI agent time and slow development.

## 🎯 Next Steps

1. **Start with conftest.py cleanup** - highest impact, lowest risk
2. **Create one local mock example** - establish the pattern
3. **Add test markers** - enable selective execution
4. **Document the new patterns** - prevent regression

This restructure will transform your test suite from a growing maintenance burden into a development accelerator that scales cleanly as your project grows.