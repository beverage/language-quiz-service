"""
CLI-specific configuration - DEPRECATED.

This module now imports from the new core configuration.
Kept for backward compatibility during migration.
"""

# Import with absolute path for CLI compatibility
import sys
from pathlib import Path

# Add the parent directory to the path for imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from core.config import settings as app_settings

# Backward compatibility - expose the settings as before
__all__ = ['app_settings'] 