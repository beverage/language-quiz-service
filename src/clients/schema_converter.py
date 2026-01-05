"""
Schema conversion utilities for Gemini API.

Converts OpenAI-style JSON schemas to Google GenAI Schema objects.
"""

import logging
from typing import Any

from google.genai import types

logger = logging.getLogger(__name__)


def convert_openai_format_to_genai_schema(
    response_format: dict[str, Any],
) -> types.Schema | None:
    """
    Convert OpenAI-style response_format to Google GenAI Schema.

    OpenAI format: {"json_schema": {"name": "...", "schema": {...}}}
    Gemini needs: types.Schema object

    Args:
        response_format: OpenAI-style response format dict

    Returns:
        Google GenAI Schema object, or None if conversion fails
    """
    if not response_format:
        return None

    try:
        # Extract the actual JSON schema from OpenAI's wrapper
        if "json_schema" in response_format:
            json_schema_wrapper = response_format["json_schema"]
            if (
                isinstance(json_schema_wrapper, dict)
                and "schema" in json_schema_wrapper
            ):
                schema = json_schema_wrapper["schema"]
            else:
                schema = json_schema_wrapper
        else:
            # Already a raw schema
            schema = response_format

        return _convert_schema_recursive(schema)

    except Exception as e:
        logger.warning(f"Schema conversion failed: {e}, returning None")
        return None


def _convert_schema_recursive(schema: dict[str, Any]) -> types.Schema:
    """
    Recursively convert schema elements to GenAI format.

    Args:
        schema: Schema dictionary to convert

    Returns:
        Converted GenAI Schema object
    """
    # Handle oneOf schemas (used for nullable fields)
    if "oneOf" in schema:
        return _convert_oneof_schema(schema)

    if "type" not in schema:
        logger.warning("Schema missing 'type' field, defaulting to STRING")
        return types.Schema(type=types.Type.STRING, nullable=False)

    schema_type = schema["type"]
    nullable = schema.get("nullable", False)

    # Handle different JSON schema types
    if schema_type == "object":
        return _convert_object_schema(schema, nullable)
    elif schema_type == "array":
        return _convert_array_schema(schema, nullable)
    elif schema_type in ["string", "integer", "number", "boolean"]:
        return _convert_primitive_schema(schema_type, schema, nullable)
    else:
        logger.warning(
            f"Unsupported schema type: {schema_type}, falling back to STRING"
        )
        return types.Schema(type=types.Type.STRING, nullable=False)


def _convert_object_schema(
    schema: dict[str, Any], nullable: bool = False
) -> types.Schema:
    """Convert object schema to GenAI format."""
    properties = {}
    required_fields = schema.get("required", [])

    # Handle properties
    if "properties" in schema:
        for prop_name, prop_schema in schema["properties"].items():
            prop_nullable = prop_name not in required_fields
            properties[prop_name] = _convert_schema_recursive(
                {**prop_schema, "nullable": prop_nullable}
            )

    return types.Schema(
        type=types.Type.OBJECT,
        properties=properties,
        required=required_fields if required_fields else None,
        nullable=nullable,
    )


def _convert_array_schema(
    schema: dict[str, Any], nullable: bool = False
) -> types.Schema:
    """Convert array schema to GenAI format."""
    # Handle items schema
    if "items" in schema:
        items_schema = _convert_schema_recursive(schema["items"])
    else:
        # Default to string items if no items schema specified
        items_schema = types.Schema(type=types.Type.STRING, nullable=False)

    return types.Schema(type=types.Type.ARRAY, items=items_schema, nullable=nullable)


def _convert_oneof_schema(schema: dict[str, Any]) -> types.Schema:
    """
    Convert oneOf schema to GenAI format.

    For schemas like: {"oneOf": [{"type": "string"}, {"type": "null"}]}
    This represents a nullable string, so we return a nullable string schema.
    """
    oneof_options = schema["oneOf"]

    # Look for the primary type (not null)
    primary_type = None
    primary_schema = None
    is_nullable = False

    for option in oneof_options:
        if option.get("type") == "null":
            is_nullable = True
        elif option.get("type") and primary_type is None:
            primary_type = option["type"]
            primary_schema = option

    # If we found a primary type, use it
    if primary_type:
        return _convert_primitive_schema(
            primary_type, primary_schema or {}, nullable=is_nullable
        )

    # Fallback to string if no clear type found
    return types.Schema(type=types.Type.STRING, nullable=is_nullable)


def _convert_primitive_schema(
    schema_type: str, schema: dict[str, Any], nullable: bool = False
) -> types.Schema:
    """Convert primitive schema types to GenAI format."""
    type_mapping = {
        "string": types.Type.STRING,
        "integer": types.Type.INTEGER,
        "number": types.Type.NUMBER,
        "boolean": types.Type.BOOLEAN,
    }

    gemini_type = type_mapping.get(schema_type, types.Type.STRING)

    # Handle enums for string types
    if schema_type == "string" and "enum" in schema:
        return types.Schema(
            type=gemini_type,
            nullable=nullable,
            enum=schema["enum"],
        )

    return types.Schema(type=gemini_type, nullable=nullable)
