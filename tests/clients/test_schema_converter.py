"""Tests for schema converter utilities."""

from unittest.mock import patch

import pytest
from google.genai import types

from src.clients.schema_converter import (
    _convert_array_schema,
    _convert_object_schema,
    _convert_oneof_schema,
    _convert_primitive_schema,
    _convert_schema_recursive,
    convert_openai_format_to_genai_schema,
)


@pytest.mark.unit
class TestConvertOpenAIFormatToGenAISchema:
    """Test the main conversion function."""

    def test_returns_none_for_empty_input(self):
        """Test that None is returned for empty/None input."""
        assert convert_openai_format_to_genai_schema(None) is None
        assert convert_openai_format_to_genai_schema({}) is None

    def test_converts_openai_wrapped_schema(self):
        """Test conversion of OpenAI-style wrapped schema."""
        openai_format = {
            "json_schema": {
                "name": "TestSchema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                    },
                },
            }
        }

        result = convert_openai_format_to_genai_schema(openai_format)

        assert result is not None
        assert result.type == types.Type.OBJECT
        assert "name" in result.properties

    def test_converts_openai_wrapped_schema_without_schema_key(self):
        """Test conversion when json_schema exists but is not a dict with schema key."""
        # Edge case: json_schema exists but is not a dict or doesn't have "schema" key
        openai_format = {
            "json_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                },
            }
        }

        result = convert_openai_format_to_genai_schema(openai_format)

        assert result is not None
        assert result.type == types.Type.OBJECT
        assert "name" in result.properties

    def test_converts_raw_schema(self):
        """Test conversion of raw schema (no wrapper)."""
        raw_schema = {
            "type": "object",
            "properties": {
                "value": {"type": "string"},
            },
        }

        result = convert_openai_format_to_genai_schema(raw_schema)

        assert result is not None
        assert result.type == types.Type.OBJECT
        assert "value" in result.properties

    def test_handles_conversion_failure_gracefully(self):
        """Test that conversion failures return None instead of raising."""
        invalid_schema = {"invalid": "schema"}

        with patch(
            "src.clients.schema_converter._convert_schema_recursive",
            side_effect=Exception("Conversion failed"),
        ):
            result = convert_openai_format_to_genai_schema(invalid_schema)

        assert result is None


@pytest.mark.unit
class TestConvertSchemaRecursive:
    """Test recursive schema conversion."""

    def test_handles_oneof_schema(self):
        """Test that oneOf schemas are handled correctly."""
        schema = {
            "oneOf": [
                {"type": "string"},
                {"type": "null"},
            ]
        }

        result = _convert_schema_recursive(schema)

        assert result.type == types.Type.STRING
        assert result.nullable is True

    def test_handles_missing_type_field(self, caplog):
        """Test that missing type field defaults to STRING."""
        schema = {"properties": {"key": {"type": "string"}}}

        result = _convert_schema_recursive(schema)

        assert result.type == types.Type.STRING
        assert "Schema missing 'type' field" in caplog.text

    def test_handles_unsupported_type(self, caplog):
        """Test that unsupported types fall back to STRING."""
        schema = {"type": "unsupported_type"}

        result = _convert_schema_recursive(schema)

        assert result.type == types.Type.STRING
        assert "Unsupported schema type" in caplog.text

    def test_converts_object_schema(self):
        """Test object schema conversion."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
        }

        result = _convert_schema_recursive(schema)

        assert result.type == types.Type.OBJECT
        assert "name" in result.properties
        assert "age" in result.properties
        assert result.properties["name"].type == types.Type.STRING
        assert result.properties["age"].type == types.Type.INTEGER

    def test_converts_array_schema(self):
        """Test array schema conversion."""
        schema = {
            "type": "array",
            "items": {"type": "string"},
        }

        result = _convert_schema_recursive(schema)

        assert result.type == types.Type.ARRAY
        assert result.items.type == types.Type.STRING

    def test_converts_primitive_schemas(self):
        """Test primitive type conversion."""
        string_schema = {"type": "string"}
        integer_schema = {"type": "integer"}
        number_schema = {"type": "number"}
        boolean_schema = {"type": "boolean"}

        assert _convert_schema_recursive(string_schema).type == types.Type.STRING
        assert _convert_schema_recursive(integer_schema).type == types.Type.INTEGER
        assert _convert_schema_recursive(number_schema).type == types.Type.NUMBER
        assert _convert_schema_recursive(boolean_schema).type == types.Type.BOOLEAN

    def test_handles_nullable_flag(self):
        """Test that nullable flag is respected."""
        schema = {"type": "string", "nullable": True}

        result = _convert_schema_recursive(schema)

        assert result.nullable is True


@pytest.mark.unit
class TestConvertObjectSchema:
    """Test object schema conversion."""

    def test_converts_simple_object(self):
        """Test conversion of simple object schema."""
        schema = {
            "properties": {
                "name": {"type": "string"},
            },
        }

        result = _convert_object_schema(schema)

        assert result.type == types.Type.OBJECT
        assert "name" in result.properties
        assert result.properties["name"].type == types.Type.STRING

    def test_handles_required_fields(self):
        """Test that required fields are marked as non-nullable."""
        schema = {
            "properties": {
                "required_field": {"type": "string"},
                "optional_field": {"type": "string"},
            },
            "required": ["required_field"],
        }

        result = _convert_object_schema(schema)

        assert result.required == ["required_field"]
        assert result.properties["required_field"].nullable is False
        assert result.properties["optional_field"].nullable is True

    def test_handles_empty_properties(self):
        """Test object with no properties."""
        schema = {"properties": {}}

        result = _convert_object_schema(schema)

        assert result.type == types.Type.OBJECT
        assert result.properties == {}

    def test_handles_nullable_object(self):
        """Test nullable object schema."""
        schema = {
            "properties": {"name": {"type": "string"}},
        }

        result = _convert_object_schema(schema, nullable=True)

        assert result.nullable is True


@pytest.mark.unit
class TestConvertArraySchema:
    """Test array schema conversion."""

    def test_converts_array_with_items_schema(self):
        """Test array with specified items schema."""
        schema = {
            "items": {"type": "integer"},
        }

        result = _convert_array_schema(schema)

        assert result.type == types.Type.ARRAY
        assert result.items.type == types.Type.INTEGER

    def test_defaults_to_string_items_when_no_items_specified(self):
        """Test that arrays default to string items when no items schema."""
        schema = {}

        result = _convert_array_schema(schema)

        assert result.type == types.Type.ARRAY
        assert result.items.type == types.Type.STRING

    def test_handles_nested_arrays(self):
        """Test nested array schemas."""
        schema = {
            "items": {
                "type": "array",
                "items": {"type": "string"},
            },
        }

        result = _convert_array_schema(schema)

        assert result.type == types.Type.ARRAY
        assert result.items.type == types.Type.ARRAY
        assert result.items.items.type == types.Type.STRING

    def test_handles_nullable_array(self):
        """Test nullable array schema."""
        schema = {"items": {"type": "string"}}

        result = _convert_array_schema(schema, nullable=True)

        assert result.nullable is True


@pytest.mark.unit
class TestConvertOneofSchema:
    """Test oneOf schema conversion (nullable fields)."""

    def test_converts_nullable_string(self):
        """Test oneOf with string and null (nullable string)."""
        schema = {
            "oneOf": [
                {"type": "string"},
                {"type": "null"},
            ]
        }

        result = _convert_oneof_schema(schema)

        assert result.type == types.Type.STRING
        assert result.nullable is True

    def test_converts_nullable_integer(self):
        """Test oneOf with integer and null."""
        schema = {
            "oneOf": [
                {"type": "integer"},
                {"type": "null"},
            ]
        }

        result = _convert_oneof_schema(schema)

        assert result.type == types.Type.INTEGER
        assert result.nullable is True

    def test_handles_null_first(self):
        """Test oneOf with null first."""
        schema = {
            "oneOf": [
                {"type": "null"},
                {"type": "string"},
            ]
        }

        result = _convert_oneof_schema(schema)

        assert result.type == types.Type.STRING
        assert result.nullable is True

    def test_fallback_to_string_when_no_primary_type(self):
        """Test fallback when no clear primary type found."""
        schema = {
            "oneOf": [
                {"type": "null"},
            ]
        }

        result = _convert_oneof_schema(schema)

        assert result.type == types.Type.STRING
        assert result.nullable is True


@pytest.mark.unit
class TestConvertPrimitiveSchema:
    """Test primitive schema conversion."""

    def test_converts_all_primitive_types(self):
        """Test all supported primitive types."""
        assert _convert_primitive_schema("string", {}).type == types.Type.STRING
        assert _convert_primitive_schema("integer", {}).type == types.Type.INTEGER
        assert _convert_primitive_schema("number", {}).type == types.Type.NUMBER
        assert _convert_primitive_schema("boolean", {}).type == types.Type.BOOLEAN

    def test_handles_enum_for_strings(self):
        """Test enum handling for string types."""
        schema = {
            "type": "string",
            "enum": ["option1", "option2", "option3"],
        }

        result = _convert_primitive_schema("string", schema)

        assert result.type == types.Type.STRING
        assert result.enum == ["option1", "option2", "option3"]

    def test_handles_nullable_primitives(self):
        """Test nullable primitive types."""
        result = _convert_primitive_schema("string", {}, nullable=True)

        assert result.nullable is True

    def test_fallback_for_unknown_type(self):
        """Test fallback to STRING for unknown types."""
        result = _convert_primitive_schema("unknown_type", {})

        assert result.type == types.Type.STRING


@pytest.mark.unit
class TestSchemaConverterIntegration:
    """Integration tests for complex schema conversions."""

    def test_converts_nested_object_schema(self):
        """Test conversion of nested object schemas."""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                    },
                },
            },
        }

        result = convert_openai_format_to_genai_schema(schema)

        assert result.type == types.Type.OBJECT
        assert "user" in result.properties
        assert result.properties["user"].type == types.Type.OBJECT
        assert "name" in result.properties["user"].properties
        assert "age" in result.properties["user"].properties

    def test_converts_array_of_objects(self):
        """Test conversion of array of objects."""
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                },
            },
        }

        result = convert_openai_format_to_genai_schema(schema)

        assert result.type == types.Type.ARRAY
        assert result.items.type == types.Type.OBJECT
        assert "id" in result.items.properties
        assert "name" in result.items.properties

    def test_converts_complex_schema_with_all_features(self):
        """Test conversion of complex schema with all features."""
        schema = {
            "type": "object",
            "properties": {
                "required_string": {"type": "string"},
                "optional_integer": {"type": "integer"},
                "nullable_string": {
                    "oneOf": [{"type": "string"}, {"type": "null"}],
                },
                "enum_field": {
                    "type": "string",
                    "enum": ["value1", "value2"],
                },
                "array_field": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["required_string"],
        }

        result = convert_openai_format_to_genai_schema(schema)

        assert result.type == types.Type.OBJECT
        assert result.required == ["required_string"]
        assert result.properties["required_string"].nullable is False
        assert result.properties["optional_integer"].nullable is True
        assert result.properties["nullable_string"].nullable is True
        assert result.properties["enum_field"].enum == ["value1", "value2"]
        assert result.properties["array_field"].type == types.Type.ARRAY
