"""Test message handler for verifying Kafka connectivity."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TestMessageHandler:
    """
    Simple test handler that logs incoming messages.

    This is used to verify that Kafka is working correctly before
    implementing the actual problem generation handler.
    """

    async def handle(self, message: dict[str, Any]) -> None:
        """
        Handle a test message by logging it.

        Args:
            message: Message payload from Kafka
        """
        logger.info(f"📨 Received test message: {message}")

        # Simulate some async work
        import asyncio

        await asyncio.sleep(0.1)

        logger.info("✅ Processed test message successfully")
