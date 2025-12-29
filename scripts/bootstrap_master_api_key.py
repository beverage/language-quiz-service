#!/usr/bin/env python3
"""
Bootstrap script to create a master API key for production.

This script directly uses the ApiKeyService to create a master API key,
bypassing the API authentication layer since no API keys exist yet.

Usage:
    python scripts/bootstrap_master_api_key.py

Environment variables:
    SUPABASE_URL: Supabase project URL (required)
    SUPABASE_SERVICE_ROLE_KEY: Supabase service role key (required)
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.schemas.api_keys import ApiKeyCreate
from src.services.api_key_service import ApiKeyService

# Add src to path so we can import modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    print("⚠️  Warning: .env file not found. Using environment variables only.")


async def bootstrap_master_key():
    """Create a master API key with admin permissions."""
    # Check required environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print(
            "❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables are required"
        )
        print("\nExample:")
        print("  export SUPABASE_URL='https://your-project.supabase.co'")
        print("  export SUPABASE_SERVICE_ROLE_KEY='your-service-role-key'")
        print("  python scripts/bootstrap_master_api_key.py")
        sys.exit(1)

    # Ensure environment variables are set for the Supabase client
    # (They should already be set, but this ensures they're available)
    os.environ["SUPABASE_URL"] = supabase_url
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = supabase_key

    try:
        # Create the API key service
        service = ApiKeyService()

        # Create master API key data
        api_key_data = ApiKeyCreate(
            name="Master API Key",
            description="Bootstrap master key for production - created via bootstrap script",
            client_name="Production Bootstrap",
            permissions_scope=["read", "write", "admin"],
            rate_limit_rpm=10000,  # High rate limit for master key
            allowed_ips=None,  # No IP restrictions for master key
        )

        print("🔑 Creating master API key...")
        print(f"   Name: {api_key_data.name}")
        print(f"   Permissions: {', '.join(api_key_data.permissions_scope)}")
        print()

        # Create the API key
        result = await service.create_api_key(api_key_data)

        # Display the result
        print("✅ Master API key created successfully!")
        print()
        print("=" * 80)
        print("🔐 MASTER API KEY (SAVE THIS SECURELY - IT WON'T BE SHOWN AGAIN)")
        print("=" * 80)
        print()
        print(result.api_key)
        print()
        print("=" * 80)
        print()
        print("Key Information:")
        print(f"   ID: {result.key_info.id}")
        print(f"   Prefix: {result.key_info.key_prefix}")
        print(f"   Name: {result.key_info.name}")
        print(f"   Permissions: {', '.join(result.key_info.permissions_scope)}")
        print(f"   Rate Limit: {result.key_info.rate_limit_rpm} requests/minute")
        print(f"   Created: {result.key_info.created_at}")
        print()
        print(
            "⚠️  IMPORTANT: Store this API key securely. It provides full admin access."
        )
        print()

    except Exception as e:
        print(f"❌ Error creating master API key: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(bootstrap_master_key())
