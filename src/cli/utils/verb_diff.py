"""Utility for comparing and displaying verb changes."""

from typing import Any


def get_verb_diff(
    before: dict[str, Any] | None, after: dict[str, Any], fields: list[str] = None
) -> dict[str, tuple[Any, Any]]:
    """
    Compare two verb dictionaries and return only the fields that changed.

    Args:
        before: Verb state before update (None if new verb)
        after: Verb state after update
        fields: List of field names to compare. If None, uses default key fields.

    Returns:
        Dict mapping field names to (old_value, new_value) tuples for changed fields only
    """
    if fields is None:
        fields = [
            "infinitive",
            "auxiliary",
            "reflexive",
            "classification",
            "can_have_cod",
            "can_have_coi",
        ]

    changes = {}

    if before is None:
        # New verb - all fields are "new"
        for field in fields:
            if field in after:
                changes[field] = (None, after[field])
    else:
        # Compare each field
        for field in fields:
            old_val = before.get(field)
            new_val = after.get(field)

            if old_val != new_val:
                changes[field] = (old_val, new_val)

    return changes


def format_verb_diff(infinitive: str, changes: dict[str, tuple[Any, Any]]) -> str:
    """
    Format verb changes for console display.

    Args:
        infinitive: Verb infinitive for the header
        changes: Dict from get_verb_diff()

    Returns:
        Formatted string for console output
    """
    if not changes:
        return ""

    lines = [f"   📝 {infinitive}:"]

    for field, (old_val, new_val) in sorted(changes.items()):
        if old_val is None:
            # New field
            lines.append(f"      {field}: [new] {new_val}")
        else:
            # Changed field
            lines.append(f"      {field}: {old_val} → {new_val}")

    return "\n".join(lines)
