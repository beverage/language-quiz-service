"""
CLI database initialization - MIGRATED.

This module now imports from the new core database initialization.
Maintained for backward compatibility during migration.
"""
import sys
from pathlib import Path

# Add the parent directory to the path for imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

# Import from new core module
from core.database_init import init_auxiliaries

# Backward compatibility - expose the functions as before
__all__ = ['init_auxiliaries']
