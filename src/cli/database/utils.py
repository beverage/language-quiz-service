"""
Database utility functions - UPDATED.

Updated to work with Pydantic models instead of SQLAlchemy.
"""

import enum
from typing import Any


def object_as_dict(obj) -> dict[str, Any]:
    """Convert an object to a dictionary for display."""
    if obj is None:
        return {}

    # Handle Pydantic models
    if hasattr(obj, "model_dump"):
        return obj.model_dump()

    # Handle regular objects with __dict__
    if hasattr(obj, "__dict__"):
        return {
            key: value for key, value in obj.__dict__.items() if not key.startswith("_")
        }

    # Handle basic types
    return {"value": obj}


class DatabaseStringEnum(enum.Enum):
    def __str__(self):
        return self.name
