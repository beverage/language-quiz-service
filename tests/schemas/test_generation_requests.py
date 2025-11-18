"""Tests for generation request schemas."""

from uuid import uuid4

import pytest

from src.schemas.generation_requests import (
    EntityType,
    GenerationRequest,
    GenerationRequestBase,
    GenerationRequestCreate,
    GenerationStatus,
)


@pytest.mark.unit
class TestGenerationRequestSchemas:
    """Test generation request schema validation."""

    def test_generation_status_enum_values(self):
        """Test all generation status enum values."""
        assert GenerationStatus.PENDING == "pending"
        assert GenerationStatus.PROCESSING == "processing"
        assert GenerationStatus.COMPLETED == "completed"
        assert GenerationStatus.PARTIAL == "partial"
        assert GenerationStatus.FAILED == "failed"

    def test_entity_type_enum_values(self):
        """Test all entity type enum values."""
        assert EntityType.PROBLEM == "problem"
        assert EntityType.SENTENCE == "sentence"
        assert EntityType.VOCABULARY == "vocabulary"

    def test_generation_request_create_defaults(self):
        """Test default values for GenerationRequestCreate."""
        request = GenerationRequestCreate(
            entity_type=EntityType.PROBLEM,
            requested_count=5,
        )

        assert request.status == GenerationStatus.PENDING
        assert request.generated_count == 0
        assert request.failed_count == 0
        assert request.constraints is None
        assert request.metadata is None

    def test_generation_request_create_with_constraints(self):
        """Test creating request with constraints."""
        constraints = {"includes_cod": True, "tenses_used": ["present"]}
        request = GenerationRequestCreate(
            entity_type=EntityType.PROBLEM,
            requested_count=3,
            constraints=constraints,
        )

        assert request.constraints == constraints

    def test_generation_request_create_with_metadata(self):
        """Test creating request with metadata."""
        metadata = {"statement_count": 4, "topic_tags": ["test"]}
        request = GenerationRequestCreate(
            entity_type=EntityType.PROBLEM,
            requested_count=2,
            metadata=metadata,
        )

        assert request.metadata == metadata

    def test_generation_request_model_serialization(self):
        """Test generation request model serialization."""
        from datetime import UTC, datetime

        request = GenerationRequest(
            id=uuid4(),
            entity_type=EntityType.PROBLEM,
            status=GenerationStatus.COMPLETED,
            requested_count=5,
            generated_count=5,
            failed_count=0,
            requested_at=datetime.now(UTC),
        )

        # Test model_dump
        data = request.model_dump()
        assert "id" in data
        assert data["entity_type"] == "problem"
        assert data["status"] == "completed"
        assert data["requested_count"] == 5

        # Test JSON serialization
        json_data = request.model_dump(mode="json")
        assert isinstance(json_data["id"], str)
