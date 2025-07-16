# tests/conftest.py
"""Shared fixtures for the test suite using local Supabase."""

import json
import os
import subprocess

import pytest


# Override environment variables IMMEDIATELY at module import time
def _setup_test_environment():
    """Set up test environment variables before any other imports."""
    # Get local Supabase service key
    try:
        result = subprocess.run(
            ["supabase", "status", "--output", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        status_data = json.loads(result.stdout)
        service_role_key = status_data.get("SERVICE_ROLE_KEY", "")

        if not service_role_key:
            raise ValueError("SERVICE_ROLE_KEY not found in supabase status output")

    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as e:
        raise RuntimeError(f"Failed to get service role key from supabase status: {e}")

    # Set test environment variables immediately
    test_env_vars = {
        "SUPABASE_URL": "http://127.0.0.1:54321",
        "SUPABASE_SERVICE_ROLE_KEY": service_role_key,
        "SUPABASE_API_URL": "http://127.0.0.1:54321",  # Override any production URL
        "SUPABASE_ANON_KEY": service_role_key,  # Use same key for tests
    }

    for key, value in test_env_vars.items():
        os.environ[key] = value


# Set up environment IMMEDIATELY when this module is imported
_setup_test_environment()

# Force reset of Settings after environment override
try:
    from src.core.config import reset_settings

    reset_settings()
except ImportError:
    # Settings module not available yet, will be reset later
    pass


@pytest.fixture
async def test_supabase_client():
    """Create a Supabase client for testing that points to local Supabase instance."""
    from src.clients.supabase import create_test_supabase_client

    # Local Supabase API connection details
    supabase_url = "http://127.0.0.1:54321"

    # Get service role key from supabase status
    try:
        result = subprocess.run(
            ["supabase", "status", "--output", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        status_data = json.loads(result.stdout)
        service_role_key = status_data.get("SERVICE_ROLE_KEY", "")

        if not service_role_key:
            raise ValueError("SERVICE_ROLE_KEY not found in supabase status output")

    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as e:
        raise RuntimeError(f"Failed to get service role key from supabase status: {e}")

    # Create and return Supabase client for local instance
    client = await create_test_supabase_client(supabase_url, service_role_key)
    yield client
    # No explicit cleanup needed - client connections are handled automatically
