# tests/conftest.py
"""Shared fixtures for the test suite using local Supabase."""

import json
import os
import subprocess

import pytest

# Force reset of Settings after environment override
# This is crucial for the FastAPI app to load with the correct test settings
from src.core.config import reset_settings
from supabase import Client, acreate_client


# Helper function to create a test client, now co-located with tests
async def create_test_supabase_client(
    database_url: str, service_key: str = "test_key"
) -> Client:
    """Create a Supabase client for testing that points to a local Supabase instance."""
    return await acreate_client(database_url, service_key)


# Override environment variables IMMEDIATELY at module import time
def _setup_test_environment():
    """Set up test environment variables before any other imports."""
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
