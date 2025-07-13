"""Unit tests for the database initialization script."""

import pytest
from unittest.mock import patch, AsyncMock
from src.cli.database.init import init_verbs, ETRE_VERBS, AVOIR_VERBS, PRONOMINAL_VERBS


@pytest.mark.asyncio
async def test_init_verbs():
    """Tests that the init_verbs function calls the verb service for all verbs."""
    with patch("src.cli.database.init.VerbService") as mock_verb_service_class:
        mock_service_instance = AsyncMock()
        mock_verb_service_class.return_value = mock_service_instance

        # Simulate some successes and some failures
        mock_service_instance.download_verb.side_effect = [
            AsyncMock(),  # Naître
            Exception("Failed to download mourir"),  # Mourir
        ] + [AsyncMock() for _ in range(len(AVOIR_VERBS) + len(PRONOMINAL_VERBS) - 1)]

        await init_verbs()

        total_verbs = len(ETRE_VERBS) + len(AVOIR_VERBS) + len(PRONOMINAL_VERBS)
        assert mock_service_instance.download_verb.call_count == total_verbs

        # Check that a failure is handled gracefully
        # (This is a simple check; more advanced would be to check log output)
        # For now, just confirming it completes is sufficient.
