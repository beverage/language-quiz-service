"""
CLI database clear operations - MIGRATED.

Migrated to use Supabase services instead of SQLAlchemy.
Maintained for backward compatibility.
"""

from clients.supabase import get_supabase_client


async def clear_database():
    """Clear all user data from the database - migrated to use Supabase."""
    client = get_supabase_client()

    # Clear tables in order (respecting foreign key constraints)
    await clear_table(client, "conjugations")
    await clear_table(client, "sentences")
    await clear_table(client, "verbs")
    await clear_table(client, "verb_groups")


async def clear_table(client, table_name):
    """Clear a specific table."""
    try:
        # Delete all rows from table
        result = client.table(table_name).delete().neq("id", 0).execute()
        print(f"Cleared table '{table_name}': {len(result.data)} rows deleted")
    except Exception as e:
        print(f"Error clearing table '{table_name}': {str(e)}")
