"""Supabase client configuration."""
from supabase import create_client, Client

# Import path setup for direct execution
import sys
from pathlib import Path

# Get paths for imports
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from core.config import settings


def get_supabase_client() -> Client:
    """Get Supabase client with service role key for backend operations."""
    return create_client(
        settings.supabase_url,
        settings.supabase_service_key
    )


async def test_supabase_connection() -> bool:
    """Test basic Supabase connectivity."""
    try:
        client = get_supabase_client()
        response = client.table('verbs').select('count', count='exact').execute()
        print(f"✅ Supabase connection successful. Verbs table has {response.count} rows.")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False 