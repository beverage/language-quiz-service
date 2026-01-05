"""Problem generation handler for worker."""

import logging
from typing import Any
from uuid import UUID

from src.core.exceptions import ValidationError
from src.core.factories import (
    create_generation_request_repository,
    create_problem_service,
)
from src.repositories.generation_requests_repository import (
    GenerationRequestRepository,
)
from src.schemas.generation_requests import GenerationStatus
from src.schemas.problems import GrammarProblemConstraints
from src.services.problem_service import ProblemService
from src.worker import metrics
from src.worker.config import worker_config
from src.worker.tracing import create_worker_span, extract_trace_context

logger = logging.getLogger(__name__)


class ProblemGenerationHandler:
    """
    Handler for problem generation messages from Kafka.

    Processes async problem generation requests by:
    1. Extracting trace context for distributed tracing
    2. Parsing message payload
    3. Generating problem using ProblemService
    4. Recording metrics and logs
    """

    def __init__(self):
        """Initialize handler with problem service and generation request repository."""
        self.problem_service: ProblemService | None = None
        self.gen_request_repo: GenerationRequestRepository | None = None

    async def _get_problem_service(self) -> ProblemService:
        """Lazily initialize problem service."""
        if self.problem_service is None:
            self.problem_service = await create_problem_service()
        return self.problem_service

    async def _get_gen_request_repo(self) -> GenerationRequestRepository:
        """Lazily initialize generation request repository."""
        if self.gen_request_repo is None:
            self.gen_request_repo = await create_generation_request_repository()
        return self.gen_request_repo

    def _validate_message(
        self, message: dict[str, Any]
    ) -> tuple[bool, str | None, UUID | None]:
        """
        Validate that message contains all required fields.

        Returns:
            Tuple of (is_valid, error_message, generation_request_id_uuid)
        """
        # Extract generation_request_id first
        generation_request_id_str = message.get("generation_request_id")
        generation_request_id_uuid = None

        if not generation_request_id_str:
            return False, "Missing required field: generation_request_id", None

        # Try to parse as UUID
        try:
            generation_request_id_uuid = UUID(generation_request_id_str)
        except (ValueError, TypeError) as e:
            return False, f"Invalid generation_request_id format: {e}", None

        # Check for statement_count
        statement_count = message.get("statement_count")
        if statement_count is None:
            return (
                False,
                "Missing required field: statement_count",
                generation_request_id_uuid,
            )

        # Validate statement_count is a positive integer
        try:
            statement_count_int = int(statement_count)
            if statement_count_int <= 0:
                return (
                    False,
                    "statement_count must be positive",
                    generation_request_id_uuid,
                )
        except (ValueError, TypeError):
            return (
                False,
                f"Invalid statement_count format: {statement_count}",
                generation_request_id_uuid,
            )

        return True, None, generation_request_id_uuid

    async def handle(
        self, message: dict[str, Any], headers: list[tuple[str, bytes]] | None = None
    ) -> None:
        """
        Handle a problem generation request from Kafka.

        Args:
            message: Message payload with generation parameters
            headers: Kafka message headers (for trace context)
        """
        # Validate message structure first
        is_valid, error_message, generation_request_id_uuid = self._validate_message(
            message
        )

        if not is_valid:
            # Log malformed message with full context
            logger.error(
                f"Malformed message received: {error_message}. "
                f"Message content: {message}"
            )

            # Increment malformed message metric
            metrics.increment_messages_malformed(
                topic=worker_config.PROBLEM_GENERATION_TOPIC,
                reason=error_message or "unknown",
            )

            # If we have a valid generation_request_id, update it to FAILED
            if generation_request_id_uuid:
                try:
                    repo = await self._get_gen_request_repo()
                    await repo.update_final_status(
                        generation_request_id_uuid,
                        GenerationStatus.FAILED,
                    )
                    await repo.increment_failed_count(
                        generation_request_id_uuid,
                        error_message=f"Malformed message: {error_message}",
                    )
                    logger.info(
                        f"Updated generation request {generation_request_id_uuid} "
                        f"to FAILED due to malformed message"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to update generation request status for malformed message: {e}"
                    )

            # Return without raising - commit offset to prevent infinite retry
            return

        # Message is valid - extract fields (we know they exist now)
        generation_request_id_str = str(generation_request_id_uuid)
        statement_count = int(message["statement_count"])

        # Extract trace context from message headers
        parent_context = extract_trace_context(headers)

        # Create worker span with parent context
        span = create_worker_span(
            "worker.generate_problem",
            parent_context=parent_context,
            attributes={
                "worker.generation_request_id": generation_request_id_str,
                "worker.statement_count": statement_count,
            },
        )

        try:
            # Update generation request status to 'processing'
            try:
                repo = await self._get_gen_request_repo()
                await repo.update_status_to_processing(generation_request_id_uuid)
                logger.info(
                    f"Updated generation request {generation_request_id_uuid} status to 'processing'"
                )
            except Exception as e:
                # Don't fail the job if we can't update status
                logger.warning(
                    f"Failed to update status to processing for {generation_request_id_uuid}: {e}"
                )

            # Parse message payload
            constraints_data = message.get("constraints")
            constraints = (
                GrammarProblemConstraints(**constraints_data)
                if constraints_data
                else None
            )
            topic_tags = message.get("topic_tags", [])

            logger.info(
                f"Processing problem generation request {generation_request_id_str} "
                f"(statement_count={statement_count})"
            )

            # Generate problem using existing service
            problem_service = await self._get_problem_service()
            problem = await problem_service.create_random_grammar_problem(
                constraints=constraints,
                statement_count=statement_count,
                additional_tags=topic_tags,
                generation_request_id=generation_request_id_uuid,
            )

            # Add success attributes to span
            if span:
                span.set_attribute("worker.problem_id", str(problem.id))
                span.set_attribute("worker.success", True)

            logger.info(
                f"Successfully generated problem {problem.id} for request {generation_request_id_str}"
            )

            # Increment generated_count on success
            try:
                repo = await self._get_gen_request_repo()
                updated_request = await repo.increment_generated_count(
                    generation_request_id_uuid
                )

                # Check if we should update final status
                if updated_request:
                    await self._check_and_update_final_status(updated_request)
            except Exception as e:
                logger.warning(
                    f"Failed to increment generated_count for {generation_request_id_uuid}: {e}"
                )

        except ValidationError as e:
            # Structural/validation errors - don't retry
            error_msg = f"ValidationError: {str(e)}"
            logger.error(
                f"Validation error for request {generation_request_id_str}: {e}",
                exc_info=True,
            )

            # Add failure attributes to span
            if span:
                span.set_attribute("worker.success", False)
                span.set_attribute("worker.error_type", "ValidationError")
                span.set_attribute("worker.error_message", str(e))

            # Update generation request to FAILED
            try:
                repo = await self._get_gen_request_repo()
                updated_request = await repo.increment_failed_count(
                    generation_request_id_uuid, error_message=error_msg
                )

                # Check if we should update final status
                if updated_request:
                    await self._check_and_update_final_status(updated_request)
            except Exception as tracking_error:
                logger.warning(
                    f"Failed to increment failed_count for {generation_request_id_uuid}: {tracking_error}"
                )

            # Don't raise - commit offset (validation errors won't be fixed by retry)
            return

        except Exception as e:
            # Transient errors (DB, LLM connectivity, etc.) - allow retry
            # Add failure attributes to span
            if span:
                span.set_attribute("worker.success", False)
                span.set_attribute("worker.error_type", type(e).__name__)
                span.set_attribute("worker.error_message", str(e))

            logger.error(
                f"Failed to generate problem for request {generation_request_id_str}: {e}",
                exc_info=True,
            )

            # Increment failed_count on failure
            try:
                repo = await self._get_gen_request_repo()
                error_msg = f"{type(e).__name__}: {str(e)}"
                updated_request = await repo.increment_failed_count(
                    generation_request_id_uuid, error_message=error_msg
                )

                # Check if we should update final status
                if updated_request:
                    await self._check_and_update_final_status(updated_request)
            except Exception as tracking_error:
                logger.warning(
                    f"Failed to increment failed_count for {generation_request_id_uuid}: {tracking_error}"
                )

            raise  # Re-raise to trigger offset non-commit (message will retry)

        finally:
            # End span
            if span:
                span.end()

    async def _check_and_update_final_status(self, request) -> None:
        """
        Check if all problems have been processed and update final status.

        Args:
            request: GenerationRequest object with current counts
        """
        total_processed = request.generated_count + request.failed_count

        # If we've processed all requested problems, set final status
        if total_processed >= request.requested_count:
            if request.generated_count == request.requested_count:
                final_status = GenerationStatus.COMPLETED
            elif request.generated_count > 0:
                final_status = GenerationStatus.PARTIAL
            else:
                final_status = GenerationStatus.FAILED

            try:
                repo = await self._get_gen_request_repo()
                await repo.update_final_status(request.id, final_status)
                logger.info(
                    f"Updated generation request {request.id} final status to '{final_status.value}' "
                    f"(generated={request.generated_count}, failed={request.failed_count})"
                )
            except Exception as e:
                logger.warning(f"Failed to update final status for {request.id}: {e}")
