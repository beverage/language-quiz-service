# tests/conftest.py
"""Shared fixtures for the test suite using local Supabase."""

import pytest


@pytest.fixture
async def test_supabase_client():
    """Create a Supabase client for testing that points to local Supabase instance."""
    import json
    import subprocess
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
