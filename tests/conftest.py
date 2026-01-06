# tests/conftest.py
"""Shared fixtures for the test suite using local Supabase."""

import json
import os
import subprocess

import pytest

# Force reset of Settings after environment override
# This is crucial for the FastAPI app to load with the correct test settings
from src.core.config import reset_settings
from src.schemas.llm_response import LLMResponse
from supabase import Client, acreate_client


def mock_llm_response(content: str) -> LLMResponse:
    """Create an LLMResponse for test mocking.

    Use this when mocking OpenAIClient.handle_request() which now returns
    LLMResponse instead of str.
    """
    return LLMResponse(
        content=content,
        model="test-model",
        response_id="test-id",
        duration_ms=0.0,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
    )


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing.

    This fixture provides a mock AbstractLLMClient that can be injected into
    services during tests, preventing real LLM calls.
    """
    from unittest.mock import AsyncMock

    from src.clients.abstract_llm_client import AbstractLLMClient

    return AsyncMock(spec=AbstractLLMClient)


# Helper function to create a test client, now co-located with tests
async def create_test_supabase_client(
    database_url: str, service_key: str = "test_key"
) -> Client:
    """Create a Supabase client for testing that points to a local Supabase instance."""
    return await acreate_client(database_url, service_key)


# Override environment variables IMMEDIATELY at module import time
def _setup_test_environment():
    """Set up test environment variables before any other imports."""
    # Skip local Supabase setup if running acceptance tests against remote service
    # Acceptance tests set both CI=true and SERVICE_URL to indicate remote testing
    if os.getenv("CI") == "true" and os.getenv("SERVICE_URL"):
        # CI acceptance tests - using remote service, no local Supabase needed
        # Just set REQUIRE_AUTH to ensure tests expect authentication
        os.environ["REQUIRE_AUTH"] = "true"
        return

    # Local testing or CI unit/integration tests - set up local Supabase connection
    try:
        result = subprocess.run(
            ["supabase", "status", "--output", "json"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        status_data = json.loads(result.stdout)
        service_role_key = status_data.get("SERVICE_ROLE_KEY")

        if not service_role_key:
            raise ValueError("SERVICE_ROLE_KEY not found in Supabase status output.")

    except (
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        ValueError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ) as e:
        pytest.fail(
            f"Critical test setup failed: Could not get Supabase service role key. Is Supabase running? Error: {e}",
            pytrace=False,
        )

    # Set test environment variables immediately
    test_env_vars = {
        "SUPABASE_URL": "http://127.0.0.1:54321",
        "SUPABASE_SERVICE_ROLE_KEY": service_role_key,
        "SUPABASE_API_URL": "http://127.0.0.1:54321",
        "SUPABASE_ANON_KEY": service_role_key,  # Use service key for anon key in tests
        "REQUIRE_AUTH": "true",  # Always require auth in tests
    }

    for key, value in test_env_vars.items():
        os.environ[key] = value


# Set up environment IMMEDIATELY when this module is imported
_setup_test_environment()

reset_settings()


@pytest.fixture
async def test_supabase_client() -> Client:
    """Fixture to provide a Supabase client for the local test instance."""
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_role_key:
        pytest.fail(
            "Supabase environment variables were not set correctly by the test setup."
        )

    return await create_test_supabase_client(supabase_url, service_role_key)


@pytest.fixture(scope="session")
async def test_keys():
    """
    Generate test API keys once at session startup.

    Creates 4 test keys in parallel using the repository layer (no auth required):
    - admin: Full admin permissions
    - write: Read/write permissions
    - read: Read-only permissions
    - inactive: Inactive key for testing auth failures

    Returns dict with plain text API keys.
    Keys are generated fresh each test session for clean state.
    """
    import asyncio

    from src.repositories.api_keys_repository import ApiKeyRepository
    from src.schemas.api_keys import ApiKeyCreate, generate_api_key, hash_api_key

    # Get Supabase client with service role (bypasses auth)
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_role_key:
        pytest.fail("Supabase environment variables not set for test key generation")

    client = await acreate_client(supabase_url, service_role_key)
    repository = ApiKeyRepository(client)

    # Generate all keys with their hashes
    admin_key, admin_prefix = generate_api_key()
    admin_hash = hash_api_key(admin_key)

    write_key, write_prefix = generate_api_key()
    write_hash = hash_api_key(write_key)

    read_key, read_prefix = generate_api_key()
    read_hash = hash_api_key(read_key)

    inactive_key, inactive_prefix = generate_api_key()
    inactive_hash = hash_api_key(inactive_key)

    # Create all keys in parallel using repository (fast!)
    admin_result, write_result, read_result, inactive_result = await asyncio.gather(
        repository.create_api_key(
            ApiKeyCreate(name="Test Admin Key", permissions_scope=["admin"]),
            admin_hash,
            admin_prefix,
        ),
        repository.create_api_key(
            ApiKeyCreate(name="Test Write Key", permissions_scope=["read", "write"]),
            write_hash,
            write_prefix,
        ),
        repository.create_api_key(
            ApiKeyCreate(name="Test Read Key", permissions_scope=["read"]),
            read_hash,
            read_prefix,
        ),
        repository.create_api_key(
            ApiKeyCreate(name="Test Inactive Key", permissions_scope=["read"]),
            inactive_hash,
            inactive_prefix,
        ),
    )

    # Deactivate the inactive key
    from src.schemas.api_keys import ApiKeyUpdate

    await repository.update_api_key(inactive_result.id, ApiKeyUpdate(is_active=False))

    # Note: Supabase AsyncClient doesn't have a close() method in this version
    # The client will be garbage collected at session end

    return {
        "admin": admin_key,
        "write": write_key,
        "read": read_key,
        "inactive": inactive_key,
    }


@pytest.fixture
def admin_headers(test_keys):
    """HTTP headers with admin API key for authenticated requests."""
    return {"X-API-Key": test_keys["admin"]}


@pytest.fixture
def write_headers(test_keys):
    """HTTP headers with write API key for authenticated requests."""
    return {"X-API-Key": test_keys["write"]}


@pytest.fixture
def read_headers(test_keys):
    """HTTP headers with read-only API key for authenticated requests."""
    return {"X-API-Key": test_keys["read"]}


@pytest.fixture
def inactive_headers(test_keys):
    """HTTP headers with inactive API key for testing auth failures."""
    return {"X-API-Key": test_keys["inactive"]}
