"""Tests for async generation endpoint error handling."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.problems import API_PREFIX
from src.main import ROUTER_PREFIX, app

PROBLEMS_PREFIX = f"{ROUTER_PREFIX}{API_PREFIX}"


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.mark.unit
class TestAsyncGenerationErrors:
    """Test error handling in async generation endpoint."""

    def test_queue_service_failure_returns_500(self, client, read_headers):
        """Test that Kafka connection failures return 500."""
        with patch("src.api.problems.QueueService") as mock_queue_class:
            mock_queue = AsyncMock()
            mock_queue.publish_problem_generation_request.side_effect = Exception(
                "Kafka connection failed"
            )
            mock_queue_class.return_value = mock_queue

            response = client.post(
                f"{PROBLEMS_PREFIX}/generate",
                headers=read_headers,
                json={"count": 1, "topic_tags": ["test_data"]},
            )

            assert response.status_code == 500
            data = response.json()
            assert "message" in data
            assert "Failed to enqueue" in data["message"]

    def test_queue_service_partial_failure(self, client, read_headers):
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
                headers=read_headers,
                json={"count": 5, "topic_tags": ["test_data"]},
            )

            # Should still return 202 - but note the count returned is what was requested (5), not enqueued (3)
            # The API returns the requested count, not the enqueued count
            assert response.status_code == 202
            data = response.json()
            assert data["count"] == 5  # Shows requested count, not actual enqueued
            assert "request_id" in data
            assert isinstance(data["request_id"], str)

    def test_get_random_no_problems_returns_404(self, client, read_headers):
        """Test GET /random returns 404 when no problems exist."""
        with patch("src.api.problems.ProblemService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_least_recently_served_problem.return_value = None
            mock_service_class.return_value = mock_service

            response = client.get(f"{PROBLEMS_PREFIX}/random", headers=read_headers)

            assert response.status_code == 404
            data = response.json()
            assert "message" in data
            assert "No problems available" in data["message"]

    def test_get_random_database_error_returns_500(self, client, read_headers):
        """Test GET /random handles database errors gracefully."""
        with patch("src.api.problems.ProblemService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_least_recently_served_problem.side_effect = Exception(
                "Database connection lost"
            )
            mock_service_class.return_value = mock_service

            response = client.get(f"{PROBLEMS_PREFIX}/random", headers=read_headers)

            assert response.status_code == 500
            data = response.json()
            assert "message" in data
            assert "Failed to retrieve" in data["message"]
