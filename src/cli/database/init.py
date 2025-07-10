"""
CLI database initialization - MIGRATED.

This module now imports from the new core database initialization.
Maintained for backward compatibility during migration.
"""

# Import from new core module
from core.database_init import init_auxiliaries

# Backward compatibility - expose the functions as before
__all__ = ["init_auxiliaries"]
