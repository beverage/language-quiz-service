"""Problem generation handler for worker."""

import logging
from typing import Any

from src.schemas.problems import GrammarProblemConstraints
from src.services.problem_service import ProblemService
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
        """Initialize handler with problem service."""
        self.problem_service = ProblemService()

    async def handle(
        self, message: dict[str, Any], headers: list[tuple[str, bytes]] | None = None
    ) -> None:
        """
        Handle a problem generation request from Kafka.

        Args:
            message: Message payload with generation parameters
            headers: Kafka message headers (for trace context)
        """
        generation_request_id = message.get("generation_request_id", "unknown")

        # Extract trace context from message headers
        parent_context = extract_trace_context(headers)

        # Create worker span with parent context
        span = create_worker_span(
            "worker.generate_problem",
            parent_context=parent_context,
            attributes={
                "worker.generation_request_id": generation_request_id,
                "worker.statement_count": message.get("statement_count", 4),
            },
        )

        try:
            # Parse message payload
            constraints_data = message.get("constraints")
            constraints = (
                GrammarProblemConstraints(**constraints_data)
                if constraints_data
                else None
            )
            statement_count = message.get("statement_count", 4)
            topic_tags = message.get("topic_tags", [])

            logger.info(
                f"Processing problem generation request {generation_request_id} "
                f"(statement_count={statement_count})"
            )

            # Generate problem using existing service
            # Parse generation_request_id from message for correlation
            from uuid import UUID

            generation_request_id_str = message.get("generation_request_id")
            generation_request_id_uuid = (
                UUID(generation_request_id_str) if generation_request_id_str else None
            )

            problem = await self.problem_service.create_random_grammar_problem(
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
                f"Successfully generated problem {problem.id} for request {generation_request_id}"
            )

        except Exception as e:
            # Add failure attributes to span
            if span:
                span.set_attribute("worker.success", False)
                span.set_attribute("worker.error_type", type(e).__name__)
                span.set_attribute("worker.error_message", str(e))

            logger.error(
                f"Failed to generate problem for request {generation_request_id}: {e}",
                exc_info=True,
            )
            raise  # Re-raise to trigger offset non-commit (message will retry)

        finally:
            # End span
            if span:
                span.end()
