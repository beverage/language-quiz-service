"""
CLI-specific configuration - DEPRECATED.

This module now imports from the new core configuration.
Kept for backward compatibility during migration.
"""

from core.config import settings as app_settings

# Backward compatibility - expose the settings as before
__all__ = ["app_settings"]
