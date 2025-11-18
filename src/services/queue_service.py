"""Queue service for publishing async job requests to Kafka."""

import json
import logging
from datetime import UTC, datetime

from aiokafka import AIOKafkaProducer

from src.repositories.generation_requests_repository import (
    GenerationRequestRepository,
)
from src.schemas.generation_requests import (
    EntityType,
    GenerationRequestCreate,
    GenerationStatus,
)
from src.schemas.problems import GrammarProblemConstraints
from src.worker.config import worker_config
from src.worker.tracing import inject_trace_context

logger = logging.getLogger(__name__)


class QueueService:
    """Service for publishing async job requests to message queue."""

    def __init__(self):
        """Initialize queue service."""
        self.producer: AIOKafkaProducer | None = None

    async def _get_producer(self) -> AIOKafkaProducer:
        """Get or create Kafka producer."""
        if self.producer is None:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=worker_config.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await self.producer.start()
            logger.info(
                f"Kafka producer started, connected to {worker_config.KAFKA_BOOTSTRAP_SERVERS}"
            )

        return self.producer

    async def publish_problem_generation_request(
        self,
        constraints: GrammarProblemConstraints | None = None,
        statement_count: int = 4,
        topic_tags: list[str] | None = None,
        count: int = 1,
        trace_context: dict | None = None,
    ) -> tuple[int, str]:
        """
        Publish problem generation requests to Kafka.

        Creates a single generation_request record and publishes N messages,
        all sharing the same generation_request_id for batch tracking.

        Args:
            constraints: Optional constraints for problem generation
            statement_count: Number of statements per problem
            topic_tags: Additional topic tags
            count: Number of problems to generate
            trace_context: OpenTelemetry trace context for distributed tracing

        Returns:
            Tuple of (enqueued_count, generation_request_id)
        """
        # Create generation request record in database
        gen_request_repo = await GenerationRequestRepository.create()
        generation_request_create = GenerationRequestCreate(
            entity_type=EntityType.PROBLEM,
            requested_count=count,
            status=GenerationStatus.PENDING,
            constraints=constraints.model_dump() if constraints else None,
            metadata={
                "statement_count": statement_count,
                "topic_tags": topic_tags or [],
            },
        )
        generation_request = await gen_request_repo.create_generation_request(
            generation_request_create
        )
        generation_request_id = str(generation_request.id)

        logger.info(
            f"Created generation request {generation_request_id} for {count} problem(s)"
        )

        producer = await self._get_producer()
        enqueued_count = 0

        # Publish N messages, all with the same generation_request_id
        for i in range(count):
            message = {
                "generation_request_id": generation_request_id,
                "constraints": constraints.model_dump() if constraints else None,
                "statement_count": statement_count,
                "topic_tags": topic_tags or [],
                "enqueued_at": datetime.now(UTC).isoformat(),
            }

            # Inject current trace context into Kafka headers
            trace_headers = inject_trace_context()
            headers = [
                (key, value.encode("utf-8")) for key, value in trace_headers.items()
            ]

            try:
                await producer.send(
                    worker_config.PROBLEM_GENERATION_TOPIC,
                    value=message,
                    headers=headers if headers else None,
                )
                enqueued_count += 1

                logger.debug(
                    f"Enqueued problem generation message {i+1}/{count} "
                    f"for request {generation_request_id}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to enqueue problem generation message: {e}", exc_info=True
                )
                # Continue trying to enqueue remaining messages

        # Ensure all messages are sent
        await producer.flush()

        logger.info(
            f"Successfully enqueued {enqueued_count}/{count} messages "
            f"for generation request {generation_request_id}"
        )

        return enqueued_count, generation_request_id

    async def close(self):
        """Close the Kafka producer."""
        if self.producer:
            await self.producer.stop()
            self.producer = None
            logger.info("Kafka producer stopped")
