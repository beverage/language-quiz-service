"""Tests for problem generation handler."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.core.exceptions import ValidationError
from src.schemas.generation_requests import GenerationRequest, GenerationStatus
from src.schemas.problems import Problem, ProblemType
from src.worker.handlers.problem_handler import ProblemGenerationHandler

pytestmark = pytest.mark.asyncio


# ============================================================================
# Fixtures and Factories
# ============================================================================


@pytest.fixture
def mock_problem_service():
    """Create a mock ProblemService for testing."""
    service = AsyncMock()
    service.create_random_grammar_problem = AsyncMock()
    return service


@pytest.fixture
def handler(mock_problem_service):
    """Create a ProblemGenerationHandler instance with mocked dependencies."""
    handler_instance = ProblemGenerationHandler()
    # Pre-set the problem service to avoid None issues in tests
    handler_instance.problem_service = mock_problem_service
    return handler_instance


@pytest.fixture
def mock_problem():
    """Factory to create mock Problem objects."""

    def _create(gen_id=None, **overrides):
        defaults = {
            "id": uuid4(),
            "problem_type": ProblemType.GRAMMAR,
            "title": "Test Problem",
            "instructions": "Test instructions",
            "correct_answer_index": 0,
            "target_language_code": "eng",
            "statements": [
                {"content": "test", "is_correct": True, "translation": "test"}
            ],
            "topic_tags": ["test"],
            "source_statement_ids": [],
            "metadata": {},
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "last_served_at": None,
            "generation_request_id": gen_id or uuid4(),
        }
        defaults.update(overrides)
        return Problem(**defaults)

    return _create


@pytest.fixture
def mock_repo():
    """Factory to create mock repository with configurable counts."""

    def _create(gen_id=None, generated=0, failed=0, requested=5):
        repo = AsyncMock()
        gen_request = MagicMock(
            id=gen_id or uuid4(),
            generated_count=generated,
            failed_count=failed,
            requested_count=requested,
        )
        repo.update_status_to_processing = AsyncMock()
        repo.increment_generated_count = AsyncMock(return_value=gen_request)
        repo.increment_failed_count = AsyncMock(return_value=gen_request)
        repo.update_final_status = AsyncMock()
        return repo

    return _create


@pytest.fixture
def valid_message():
    """Factory to create valid message dictionaries."""

    def _create(gen_id=None, statement_count=4, **kwargs):
        message = {
            "generation_request_id": str(gen_id or uuid4()),
            "statement_count": statement_count,
        }
        message.update(kwargs)
        return message

    return _create


@pytest.fixture
def failing_repo():
    """Factory to create a mock repository that fails on all operations."""

    def _create(gen_id=None, exception_msg="Database error"):
        repo = AsyncMock()
        repo.update_status_to_processing.side_effect = Exception(exception_msg)
        repo.increment_generated_count.side_effect = Exception(exception_msg)
        repo.increment_failed_count.side_effect = Exception(exception_msg)
        repo.update_final_status.side_effect = Exception(exception_msg)
        return repo

    return _create


class TestProblemGenerationHandler:
    """Test problem generation message handler."""

    async def test_handle_message_success(self, handler, mock_problem, valid_message):
        """Test successful problem generation from message."""
        problem = mock_problem()

        # Mock the generation request repository
        with (
            patch.object(
                handler.problem_service,
                "create_random_grammar_problem",
                new=AsyncMock(return_value=problem),
            ) as mock_create,
            patch.object(
                handler,
                "_get_gen_request_repo",
                new=AsyncMock(return_value=AsyncMock()),
            ),
        ):
            message = valid_message(
                topic_tags=["test"], enqueued_at="2025-11-11T00:00:00Z"
            )

            # Should not raise
            await handler.handle(message, headers=None)

            # Verify service was called
            mock_create.assert_called_once()

    async def test_handle_message_with_constraints(
        self, handler, mock_problem, valid_message
    ):
        """Test message with constraints is parsed correctly."""
        problem = mock_problem(topic_tags=[])

        # Mock the generation request repository
        with (
            patch.object(
                handler.problem_service,
                "create_random_grammar_problem",
                new=AsyncMock(return_value=problem),
            ) as mock_create,
            patch.object(
                handler,
                "_get_gen_request_repo",
                new=AsyncMock(return_value=AsyncMock()),
            ),
        ):
            message = valid_message(
                statement_count=6,
                constraints={
                    "grammatical_focus": ["direct_objects"],
                    "includes_cod": True,
                },
                topic_tags=["food"],
                enqueued_at="2025-11-11T00:00:00Z",
            )

            await handler.handle(message, headers=None)

            # Verify constraints were parsed and passed
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["statement_count"] == 6
            assert call_kwargs["additional_tags"] == ["food"]
            assert call_kwargs["constraints"] is not None

    async def test_handle_message_failure_raises(self, handler, valid_message):
        """Test that handler raises exceptions on transient failures (for retry logic)."""
        # Mock the generation request repository
        with (
            patch.object(
                handler.problem_service,
                "create_random_grammar_problem",
                side_effect=Exception("LLM error"),
            ),
            patch.object(
                handler,
                "_get_gen_request_repo",
                new=AsyncMock(return_value=AsyncMock()),
            ),
        ):
            message = valid_message(
                constraints=None, topic_tags=[], enqueued_at="2025-11-11T00:00:00Z"
            )

            # Should raise to trigger message retry
            with pytest.raises(Exception):
                await handler.handle(message, headers=None)


class TestMessageValidation:
    """Test message validation logic."""

    def test_validate_message_success(self, handler, valid_message):
        """Valid message with all required fields passes validation."""
        message = valid_message()

        is_valid, error_msg, gen_id = handler._validate_message(message)

        assert is_valid is True
        assert error_msg is None
        assert gen_id is not None

    def test_validate_message_missing_generation_request_id(self, handler):
        """Missing generation_request_id is detected."""
        message = {"statement_count": 4}

        is_valid, error_msg, gen_id = handler._validate_message(message)

        assert is_valid is False
        assert "Missing required field: generation_request_id" in error_msg
        assert gen_id is None

    def test_validate_message_missing_statement_count(self, handler):
        """Missing statement_count is detected."""
        message = {"generation_request_id": str(uuid4())}

        is_valid, error_msg, gen_id = handler._validate_message(message)

        assert is_valid is False
        assert "Missing required field: statement_count" in error_msg
        assert gen_id is not None  # UUID was valid before we checked statement_count

    def test_validate_message_invalid_uuid_format(self, handler):
        """Invalid UUID format is detected."""
        message = {
            "generation_request_id": "not-a-uuid",
            "statement_count": 4,
        }

        is_valid, error_msg, gen_id = handler._validate_message(message)

        assert is_valid is False
        assert "Invalid generation_request_id format" in error_msg
        assert gen_id is None

    @pytest.mark.parametrize(
        "statement_count,expected_error",
        [
            (-5, "statement_count must be positive"),
            (0, "statement_count must be positive"),
            ("four", "Invalid statement_count format"),
        ],
    )
    def test_validate_message_invalid_statement_count(
        self, handler, statement_count, expected_error
    ):
        """Invalid statement_count values are rejected."""
        message = {
            "generation_request_id": str(uuid4()),
            "statement_count": statement_count,
        }

        is_valid, error_msg, gen_id = handler._validate_message(message)

        assert is_valid is False
        assert expected_error in error_msg


class TestMalformedMessageHandling:
    """Test handling of malformed messages."""

    async def test_malformed_message_without_generation_request_id(self, handler):
        """Malformed message without generation_request_id doesn't retry."""
        message = {"statement_count": 4}

        # Mock metrics to verify malformed message was tracked
        with patch("src.worker.handlers.problem_handler.metrics") as mock_metrics:
            # Should return without raising (commits offset)
            await handler.handle(message, headers=None)

            # Verify malformed metric was incremented
            mock_metrics.increment_messages_malformed.assert_called_once()
            assert "generation_request_id" in str(
                mock_metrics.increment_messages_malformed.call_args
            )

    async def test_malformed_message_with_invalid_uuid(self, handler):
        """Invalid UUID increments malformed metric and doesn't retry."""
        message = {
            "generation_request_id": "not-a-uuid",
            "statement_count": 4,
        }

        # Mock metrics to verify malformed message was tracked
        with patch("src.worker.handlers.problem_handler.metrics") as mock_metrics:
            # Should return without raising
            await handler.handle(message, headers=None)

            # Verify malformed metric was incremented
            mock_metrics.increment_messages_malformed.assert_called_once()

    async def test_malformed_message_with_invalid_statement_count(
        self, handler, mock_repo
    ):
        """Malformed message with valid UUID but invalid statement_count updates to FAILED."""
        gen_id = uuid4()
        repo = mock_repo(gen_id=gen_id, failed=1, requested=1)

        with patch.object(handler, "_get_gen_request_repo", return_value=repo):
            message = {
                "generation_request_id": str(gen_id),
                "statement_count": "invalid",
            }

            # Should return without raising
            await handler.handle(message, headers=None)

            # Verify generation request was updated
            repo.update_final_status.assert_called_once()
            repo.increment_failed_count.assert_called_once()


class TestValidationErrorHandling:
    """Test handling of validation errors."""

    async def test_validation_error_doesnt_retry(
        self, handler, mock_repo, valid_message
    ):
        """ValidationError doesn't retry (commits offset)."""
        gen_id = uuid4()
        repo = mock_repo(gen_id=gen_id, failed=1, requested=1)

        # Mock problem service to raise ValidationError
        with (
            patch.object(
                handler.problem_service,
                "create_random_grammar_problem",
                side_effect=ValidationError(
                    "Invalid constraints", details={"constraint": "invalid"}
                ),
            ),
            patch.object(handler, "_get_gen_request_repo", return_value=repo),
        ):
            message = valid_message(gen_id=gen_id)

            # Should NOT raise (commits offset)
            await handler.handle(message, headers=None)

            # Verify failed_count was incremented
            repo.increment_failed_count.assert_called_once()


class TestTransientErrorHandling:
    """Test handling of transient errors."""

    async def test_transient_error_raises_for_retry(
        self, handler, mock_repo, valid_message
    ):
        """Transient errors (LLM timeout, database errors) trigger retry."""
        gen_id = uuid4()
        repo = mock_repo(gen_id=gen_id)

        # Mock problem service to raise generic exception (covers LLM timeouts, database errors, etc.)
        with (
            patch.object(
                handler.problem_service,
                "create_random_grammar_problem",
                side_effect=Exception(
                    "Transient error: LLM timeout or database connection lost"
                ),
            ),
            patch.object(handler, "_get_gen_request_repo", return_value=repo),
        ):
            message = valid_message(gen_id=gen_id)

            # Should raise to trigger retry
            with pytest.raises(Exception):
                await handler.handle(message, headers=None)

            # Verify failed_count was still incremented
            repo.increment_failed_count.assert_called_once()


class TestGenerationRequestTracking:
    """Test generation request status tracking."""

    async def test_successful_generation_updates_generated_count(
        self, handler, mock_problem, mock_repo, valid_message
    ):
        """Successful generation increments generated_count."""
        gen_id = uuid4()
        problem = mock_problem(gen_id=gen_id)
        repo = mock_repo(gen_id=gen_id, generated=1, failed=0, requested=5)

        with (
            patch.object(
                handler.problem_service,
                "create_random_grammar_problem",
                new=AsyncMock(return_value=problem),
            ),
            patch.object(handler, "_get_gen_request_repo", return_value=repo),
        ):
            message = valid_message(gen_id=gen_id)

            await handler.handle(message, headers=None)

            # Verify generated_count was incremented
            repo.increment_generated_count.assert_called_once_with(gen_id)

    async def test_failed_generation_updates_failed_count(
        self, handler, mock_repo, valid_message
    ):
        """Failed generation updates failed_count and error_message."""
        gen_id = uuid4()
        repo = mock_repo(gen_id=gen_id, generated=0, failed=1, requested=1)

        with (
            patch.object(
                handler.problem_service,
                "create_random_grammar_problem",
                side_effect=Exception("Test error"),
            ),
            patch.object(handler, "_get_gen_request_repo", return_value=repo),
        ):
            message = valid_message(gen_id=gen_id)

            # Should raise
            with pytest.raises(Exception):
                await handler.handle(message, headers=None)

            # Verify failed_count was incremented with error message
            call_args = repo.increment_failed_count.call_args
            assert call_args[0][0] == gen_id
            assert "Test error" in call_args[1]["error_message"]

    async def test_status_updates_to_processing(
        self, handler, mock_problem, mock_repo, valid_message
    ):
        """Generation request status updates to processing when handler starts."""
        gen_id = uuid4()
        problem = mock_problem(gen_id=gen_id)
        repo = mock_repo(gen_id=gen_id, generated=1, failed=0, requested=5)

        with (
            patch.object(
                handler.problem_service,
                "create_random_grammar_problem",
                new=AsyncMock(return_value=problem),
            ),
            patch.object(handler, "_get_gen_request_repo", return_value=repo),
        ):
            message = valid_message(gen_id=gen_id)

            await handler.handle(message, headers=None)

            # Verify status was updated to processing
            repo.update_status_to_processing.assert_called_once_with(gen_id)

    async def test_final_status_completed_all_success(
        self, handler, mock_problem, mock_repo, valid_message
    ):
        """Final status set to COMPLETED when all problems succeed."""
        gen_id = uuid4()
        problem = mock_problem(gen_id=gen_id)
        repo = mock_repo(
            gen_id=gen_id, generated=5, failed=0, requested=5
        )  # All succeeded

        with (
            patch.object(
                handler.problem_service,
                "create_random_grammar_problem",
                new=AsyncMock(return_value=problem),
            ),
            patch.object(handler, "_get_gen_request_repo", return_value=repo),
        ):
            message = valid_message(gen_id=gen_id)

            await handler.handle(message, headers=None)

            # Verify final status was set to COMPLETED
            repo.update_final_status.assert_called_once_with(
                gen_id, GenerationStatus.COMPLETED
            )

    async def test_final_status_partial_some_fail(
        self, handler, mock_problem, mock_repo, valid_message
    ):
        """Final status set to PARTIAL when some problems fail."""
        gen_id = uuid4()
        problem = mock_problem(gen_id=gen_id)
        repo = mock_repo(
            gen_id=gen_id, generated=3, failed=2, requested=5
        )  # 3 succeeded, 2 failed

        with (
            patch.object(
                handler.problem_service,
                "create_random_grammar_problem",
                new=AsyncMock(return_value=problem),
            ),
            patch.object(handler, "_get_gen_request_repo", return_value=repo),
        ):
            message = valid_message(gen_id=gen_id)

            await handler.handle(message, headers=None)

            # Verify final status was set to PARTIAL
            repo.update_final_status.assert_called_once_with(
                gen_id, GenerationStatus.PARTIAL
            )

    async def test_final_status_failed_all_fail(
        self, handler, mock_repo, valid_message
    ):
        """Final status set to FAILED when all problems fail."""
        gen_id = uuid4()
        repo = mock_repo(
            gen_id=gen_id, generated=0, failed=5, requested=5
        )  # All failed

        with (
            patch.object(
                handler.problem_service,
                "create_random_grammar_problem",
                side_effect=Exception("Test error"),
            ),
            patch.object(handler, "_get_gen_request_repo", return_value=repo),
        ):
            message = valid_message(gen_id=gen_id)

            # Should raise
            with pytest.raises(Exception):
                await handler.handle(message, headers=None)

            # Verify final status was set to FAILED
            repo.update_final_status.assert_called_once_with(
                gen_id, GenerationStatus.FAILED
            )


class TestRepositoryFailureHandling:
    """Test handling of repository operation failures."""

    async def test_increment_generated_count_fails_after_successful_generation(
        self, handler, mock_problem, failing_repo, valid_message
    ):
        """Repository failure when incrementing generated_count doesn't prevent problem generation."""
        gen_id = uuid4()
        problem = mock_problem(gen_id=gen_id)
        repo = failing_repo(gen_id=gen_id)

        with (
            patch.object(
                handler.problem_service,
                "create_random_grammar_problem",
                new=AsyncMock(return_value=problem),
            ),
            patch.object(handler, "_get_gen_request_repo", return_value=repo),
        ):
            message = valid_message(gen_id=gen_id)

            # Should not raise - problem was still generated successfully
            await handler.handle(message, headers=None)

            # Verify problem generation was attempted
            repo.increment_generated_count.assert_called_once()

    async def test_increment_failed_count_fails_during_error_handling(
        self, handler, failing_repo, valid_message
    ):
        """Repository failure when incrementing failed_count still raises original exception."""
        gen_id = uuid4()
        repo = failing_repo(gen_id=gen_id)

        with (
            patch.object(
                handler.problem_service,
                "create_random_grammar_problem",
                side_effect=Exception("LLM error"),
            ),
            patch.object(handler, "_get_gen_request_repo", return_value=repo),
        ):
            message = valid_message(gen_id=gen_id)

            # Should still raise the original LLM error
            with pytest.raises(Exception, match="LLM error"):
                await handler.handle(message, headers=None)

    async def test_update_status_to_processing_failure_doesnt_prevent_generation(
        self, handler, mock_problem, failing_repo, valid_message
    ):
        """Problem generation continues even if status update to PROCESSING fails."""
        gen_id = uuid4()
        problem = mock_problem(gen_id=gen_id)
        repo = failing_repo(gen_id=gen_id)

        with (
            patch.object(
                handler.problem_service,
                "create_random_grammar_problem",
                new=AsyncMock(return_value=problem),
            ),
            patch.object(handler, "_get_gen_request_repo", return_value=repo),
        ):
            message = valid_message(gen_id=gen_id)

            # Should not raise - generation continues despite status update failure
            await handler.handle(message, headers=None)

            # Verify we attempted to update and incremented success count
            repo.update_status_to_processing.assert_called_once()
            repo.increment_generated_count.assert_called_once()

    async def test_update_final_status_failure_is_logged_not_raised(
        self, handler, mock_problem, mock_repo, valid_message
    ):
        """Final status update failure is logged but doesn't prevent completion."""
        gen_id = uuid4()
        problem = mock_problem(gen_id=gen_id)
        repo = mock_repo(gen_id=gen_id, generated=5, failed=0, requested=5)

        # Make update_final_status fail
        repo.update_final_status.side_effect = Exception("Database error")

        with (
            patch.object(
                handler.problem_service,
                "create_random_grammar_problem",
                new=AsyncMock(return_value=problem),
            ),
            patch.object(handler, "_get_gen_request_repo", return_value=repo),
        ):
            message = valid_message(gen_id=gen_id)

            # Should not raise - final status update failure is non-fatal
            await handler.handle(message, headers=None)

            # Verify we attempted to update final status
            repo.update_final_status.assert_called_once()

    async def test_malformed_message_with_repo_failure(self, handler, failing_repo):
        """Malformed message handling continues even if repo update fails."""
        gen_id = uuid4()
        repo = failing_repo(gen_id=gen_id)

        with (
            patch.object(handler, "_get_gen_request_repo", return_value=repo),
            patch("src.worker.handlers.problem_handler.metrics") as mock_metrics,
        ):
            message = {
                "generation_request_id": str(gen_id),
                "statement_count": "invalid",  # Malformed
            }

            # Should not raise - handler swallows repo errors for malformed messages
            await handler.handle(message, headers=None)

            # Verify malformed metric was still incremented
            mock_metrics.increment_messages_malformed.assert_called_once()


class TestTracingEdgeCases:
    """Test tracing/span handling edge cases."""

    @pytest.mark.parametrize(
        "test_scenario",
        [
            ("success", "Successful generation with None span doesn't cause errors."),
            (
                "validation_error",
                "ValidationError with None span doesn't cause errors.",
            ),
        ],
    )
    async def test_none_span_scenarios(
        self, handler, mock_problem, mock_repo, valid_message, test_scenario
    ):
        """Test that None span is handled gracefully in all code paths."""
        scenario, docstring = test_scenario
        gen_id = uuid4()
        repo = mock_repo(
            gen_id=gen_id,
            generated=1 if scenario == "success" else 0,
            failed=1 if scenario == "validation_error" else 0,
            requested=1,
        )

        if scenario == "success":
            problem = mock_problem(gen_id=gen_id)
            side_effect_or_value = AsyncMock(return_value=problem)
        else:  # validation_error
            side_effect_or_value = ValidationError(
                "Invalid constraints", details={"error": "test"}
            )

        with (
            patch.object(
                handler.problem_service,
                "create_random_grammar_problem",
                new=side_effect_or_value
                if scenario == "success"
                else MagicMock(side_effect=side_effect_or_value),
            ),
            patch.object(handler, "_get_gen_request_repo", return_value=repo),
            patch(
                "src.worker.handlers.problem_handler.create_worker_span",
                return_value=None,
            ),
        ):
            message = valid_message(gen_id=gen_id)

            # Should not raise - None span is handled
            await handler.handle(message, headers=None)

            # Verify appropriate count was incremented
            if scenario == "success":
                repo.increment_generated_count.assert_called_once()
            else:
                repo.increment_failed_count.assert_called_once()

    async def test_transient_error_with_none_span(
        self, handler, mock_repo, valid_message
    ):
        """Transient error with None span doesn't cause additional errors."""
        gen_id = uuid4()
        repo = mock_repo(gen_id=gen_id)

        with (
            patch.object(
                handler.problem_service,
                "create_random_grammar_problem",
                side_effect=Exception("LLM timeout"),
            ),
            patch.object(handler, "_get_gen_request_repo", return_value=repo),
            patch(
                "src.worker.handlers.problem_handler.create_worker_span",
                return_value=None,
            ),
        ):
            message = valid_message(gen_id=gen_id)

            # Should raise the original error
            with pytest.raises(Exception, match="LLM timeout"):
                await handler.handle(message, headers=None)

            # Verify failed count was still incremented
            repo.increment_failed_count.assert_called_once()


class TestConstraintParsing:
    """Test constraint parsing edge cases."""

    async def test_empty_constraints_dict(
        self, handler, mock_problem, mock_repo, valid_message
    ):
        """Empty constraints dict evaluates to falsy and results in None."""
        gen_id = uuid4()
        problem = mock_problem(gen_id=gen_id)
        repo = mock_repo(gen_id=gen_id, generated=1)

        with (
            patch.object(
                handler.problem_service,
                "create_random_grammar_problem",
                new=AsyncMock(return_value=problem),
            ) as mock_create,
            patch.object(handler, "_get_gen_request_repo", return_value=repo),
        ):
            message = valid_message(gen_id=gen_id, constraints={})

            await handler.handle(message, headers=None)

            # Verify problem service was called with None constraints
            call_kwargs = mock_create.call_args.kwargs
            # Empty dict is falsy, so constraints becomes None
            assert call_kwargs["constraints"] is None

    async def test_invalid_constraints_raises_validation_error(
        self, handler, mock_repo, valid_message
    ):
        """Invalid constraints data raises ValidationError during parsing."""
        gen_id = uuid4()
        repo = mock_repo(gen_id=gen_id, failed=1, requested=1)

        # GrammarProblemConstraints validation will fail with invalid data
        with (
            patch(
                "src.worker.handlers.problem_handler.GrammarProblemConstraints",
                side_effect=ValidationError(
                    "Invalid constraint", details={"field": "invalid"}
                ),
            ),
            patch.object(handler, "_get_gen_request_repo", return_value=repo),
        ):
            message = valid_message(gen_id=gen_id, constraints={"invalid": "data"})

            # Should not raise - ValidationError is caught and handled
            await handler.handle(message, headers=None)

            # Verify failed count was incremented
            repo.increment_failed_count.assert_called_once()


class TestStatusDeterminationEdgeCases:
    """Test edge cases in final status determination."""

    async def test_over_delivery_scenario(self, handler):
        """Status calculation when total_processed exceeds requested_count."""
        # Create a mock request with over-delivery
        mock_request = MagicMock(
            id=uuid4(),
            generated_count=6,
            failed_count=1,
            requested_count=5,  # Total processed (7) > requested (5)
        )

        repo = AsyncMock()

        with patch.object(handler, "_get_gen_request_repo", return_value=repo):
            await handler._check_and_update_final_status(mock_request)

            # Should update to PARTIAL since not all succeeded
            repo.update_final_status.assert_called_once_with(
                mock_request.id, GenerationStatus.PARTIAL
            )

    async def test_no_counts_but_method_called(self, handler):
        """Status calculation when called with zero counts."""
        # Edge case: somehow called with 0/0/0
        mock_request = MagicMock(
            id=uuid4(),
            generated_count=0,
            failed_count=0,
            requested_count=0,
        )

        repo = AsyncMock()

        with patch.object(handler, "_get_gen_request_repo", return_value=repo):
            await handler._check_and_update_final_status(mock_request)

            # With 0/0/0, generated_count (0) == requested_count (0) is True
            # So it sets to COMPLETED (edge case, but that's what the logic does)
            repo.update_final_status.assert_called_once_with(
                mock_request.id, GenerationStatus.COMPLETED
            )
