"""Unit tests for the database initialization script."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.cli.database.init import (
    AVOIR_VERBS,
    COI_TEST_VERBS,
    ETRE_VERBS,
    PRONOMINAL_VERBS,
    init_verbs,
)


@pytest.mark.asyncio
async def test_init_verbs():
    """Tests that the init_verbs function calls the verb service for all verbs."""
    with patch("src.cli.database.init.VerbService") as mock_verb_service_class:
        mock_service_instance = AsyncMock()
        mock_verb_service_class.return_value = mock_service_instance

        # Create a mock verb object to return from successful downloads
        mock_verb = MagicMock()
        mock_verb.infinitive = "test"

        # Simulate some successes and some failures
        mock_service_instance.download_verb.side_effect = [
            mock_verb,  # Naître
            Exception("Failed to download mourir"),  # Mourir
        ] + [
            mock_verb
            for _ in range(
                len(AVOIR_VERBS) + len(PRONOMINAL_VERBS) + len(COI_TEST_VERBS) - 1
            )
        ]

        await init_verbs()

        total_verbs = (
            len(ETRE_VERBS)
            + len(AVOIR_VERBS)
            + len(PRONOMINAL_VERBS)
            + len(COI_TEST_VERBS)
        )
        assert mock_service_instance.download_verb.call_count == total_verbs

        # Check that a failure is handled gracefully
        # (This is a simple check; more advanced would be to check log output)
        # For now, just confirming it completes is sufficient.
