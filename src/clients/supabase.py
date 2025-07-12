"""Supabase client configuration."""

from supabase import acreate_client, Client

from src.core.config import settings


async def get_supabase_client() -> Client:
    """Get Supabase client with service role key for backend operations."""
    return await acreate_client(settings.supabase_url, settings.supabase_service_key)


async def test_supabase_connection() -> bool:
    """Test basic Supabase connectivity."""
    try:
        client = await get_supabase_client()
        response = await client.table("verbs").select("count", count="exact").execute()
        print(
            f"✅ Supabase connection successful. Verbs table has {response.count} rows."
        )
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False
