"""Tests for problem generation handler."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.schemas.problems import Problem, ProblemType
from src.worker.handlers.problem_handler import ProblemGenerationHandler

pytestmark = pytest.mark.asyncio


class TestProblemGenerationHandler:
    """Test problem generation message handler."""

    async def test_handle_message_success(self):
        """Test successful problem generation from message."""
        handler = ProblemGenerationHandler()

        # Mock the problem service
        mock_problem = Problem(
            id=uuid4(),
            problem_type=ProblemType.GRAMMAR,
            title="Test Problem",
            instructions="Test instructions",
            correct_answer_index=0,
            target_language_code="eng",
            statements=[{"content": "test", "is_correct": True, "translation": "test"}],
            topic_tags=["test"],
            source_statement_ids=[],
            metadata={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_served_at=None,
            request_id=uuid4(),
        )

        with patch.object(
            handler.problem_service,
            "create_random_grammar_problem",
            return_value=mock_problem,
        ) as mock_create:
            message = {
                "request_id": str(uuid4()),
                "constraints": None,
                "statement_count": 4,
                "topic_tags": ["test"],
                "enqueued_at": "2025-11-11T00:00:00Z",
            }

            # Should not raise
            await handler.handle(message, headers=None)

            # Verify service was called
            mock_create.assert_called_once()

    async def test_handle_message_with_constraints(self):
        """Test message with constraints is parsed correctly."""
        handler = ProblemGenerationHandler()

        mock_problem = Problem(
            id=uuid4(),
            problem_type=ProblemType.GRAMMAR,
            title="Test",
            instructions="Test",
            correct_answer_index=0,
            target_language_code="eng",
            statements=[{"content": "test", "is_correct": True, "translation": "test"}],
            topic_tags=[],
            source_statement_ids=[],
            metadata={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_served_at=None,
            request_id=uuid4(),
        )

        with patch.object(
            handler.problem_service,
            "create_random_grammar_problem",
            return_value=mock_problem,
        ) as mock_create:
            message = {
                "request_id": str(uuid4()),
                "constraints": {
                    "grammatical_focus": ["direct_objects"],
                    "includes_cod": True,
                },
                "statement_count": 6,
                "topic_tags": ["food"],
                "enqueued_at": "2025-11-11T00:00:00Z",
            }

            await handler.handle(message, headers=None)

            # Verify constraints were parsed and passed
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["statement_count"] == 6
            assert call_kwargs["additional_tags"] == ["food"]
            assert call_kwargs["constraints"] is not None

    async def test_handle_message_failure_raises(self):
        """Test that handler raises exceptions on failure (for retry logic)."""
        handler = ProblemGenerationHandler()

        with patch.object(
            handler.problem_service,
            "create_random_grammar_problem",
            side_effect=Exception("LLM error"),
        ):
            message = {
                "request_id": str(uuid4()),
                "constraints": None,
                "statement_count": 4,
                "topic_tags": [],
                "enqueued_at": "2025-11-11T00:00:00Z",
            }

            # Should raise to trigger message retry
            with pytest.raises(Exception):
                await handler.handle(message, headers=None)
