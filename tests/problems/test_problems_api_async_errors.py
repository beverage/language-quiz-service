"""Tests for async generation endpoint error handling.

These tests focus on error handling behavior in the problems API.
Service dependencies are mocked via dependency overrides.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.problems import API_PREFIX
from src.main import ROUTER_PREFIX, app

PROBLEMS_PREFIX = f"{ROUTER_PREFIX}{API_PREFIX}"


# =============================================================================
# Error-Raising Mock Services
# =============================================================================


class ErrorRaisingProblemService:
    """Mock problem service that raises errors."""

    def __init__(self, error: Exception = None):
        self.error = error

    async def get_least_recently_served_problem(self, filters=None):
        """Mock that raises the configured error."""
        if self.error:
            raise self.error
        return None  # No problems found

    async def get_problem_by_id(self, problem_id):
        """Mock get problem by ID."""
        if self.error:
            raise self.error
        return None

    async def close(self):
        """Mock close."""
        pass


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def client(monkeypatch):
    """Create a test client with auth disabled."""
    from src.core.config import reset_settings

    monkeypatch.setenv("REQUIRE_AUTH", "false")
    monkeypatch.setenv("ENVIRONMENT", "development")
    reset_settings()

    yield TestClient(app)

    app.dependency_overrides.clear()
    reset_settings()


# =============================================================================
# Tests
# =============================================================================


@pytest.mark.unit
class TestAsyncGenerationErrors:
    """Test error handling in async generation endpoint."""

    def test_queue_service_failure_returns_500(self, client):
        """Test that Kafka connection failures return 500."""
        with patch("src.api.problems.QueueService") as mock_queue_class:
            mock_queue = AsyncMock()
            mock_queue.publish_problem_generation_request.side_effect = Exception(
                "Kafka connection failed"
            )
            mock_queue_class.return_value = mock_queue

            response = client.post(
                f"{PROBLEMS_PREFIX}/generate",
                json={"count": 1, "topic_tags": ["test_data"]},
            )

            assert response.status_code == 500
            data = response.json()
            assert "message" in data
            assert "Failed to enqueue" in data["message"]

    def test_queue_service_partial_failure(self, client):
        """Test handling when some messages fail to enqueue."""
        with patch("src.api.problems.QueueService") as mock_queue_class:
            mock_queue = AsyncMock()
            # Return fewer than requested (only 3 succeeded) with single request_id
            mock_queue.publish_problem_generation_request.return_value = (
                3,
                "550e8400-e29b-41d4-a716-446655440000",
            )
            mock_queue_class.return_value = mock_queue

            response = client.post(
                f"{PROBLEMS_PREFIX}/generate",
                json={"count": 5, "topic_tags": ["test_data"]},
            )

            # Should still return 202 - but note the count returned is what was requested (5), not enqueued (3)
            # The API returns the requested count, not the enqueued count
            assert response.status_code == 202
            data = response.json()
            assert data["count"] == 5  # Shows requested count, not actual enqueued
            assert "request_id" in data
            assert isinstance(data["request_id"], str)

    def test_get_random_no_problems_returns_404(self, client, monkeypatch):
        """Test GET /random returns 404 when no problems exist."""
        from src.core.config import reset_settings
        from src.core.dependencies import get_problem_service

        # Create mock service that returns None (no problems)
        mock_service = ErrorRaisingProblemService(error=None)

        monkeypatch.setenv("REQUIRE_AUTH", "false")
        monkeypatch.setenv("ENVIRONMENT", "development")
        reset_settings()

        app.dependency_overrides[get_problem_service] = lambda: mock_service

        response = client.get(f"{PROBLEMS_PREFIX}/random")

        assert response.status_code == 404
        data = response.json()
        assert "message" in data
        assert "No problems available" in data["message"]

        app.dependency_overrides.clear()
        reset_settings()

    def test_get_random_database_error_returns_500(self, client, monkeypatch):
        """Test GET /random handles database errors gracefully."""
        from src.core.config import reset_settings
        from src.core.dependencies import get_problem_service

        # Create mock service that raises an error
        mock_service = ErrorRaisingProblemService(
            error=Exception("Database connection lost")
        )

        monkeypatch.setenv("REQUIRE_AUTH", "false")
        monkeypatch.setenv("ENVIRONMENT", "development")
        reset_settings()

        app.dependency_overrides[get_problem_service] = lambda: mock_service

        response = client.get(f"{PROBLEMS_PREFIX}/random")

        assert response.status_code == 500
        data = response.json()
        assert "message" in data
        assert "Failed to retrieve" in data["message"]

        app.dependency_overrides.clear()
        reset_settings()
