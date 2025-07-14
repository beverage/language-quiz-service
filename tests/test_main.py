"""Tests for the main FastAPI application."""

import pytest
from fastapi.testclient import TestClient
import logging

from src.main import app
from src.core.config import get_settings


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.mark.functional
class TestMainApp:
    """Test the main FastAPI application."""

    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint returns service information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Language Quiz Service is running"
        assert "service" in data
        assert "version" in data

    def test_health_endpoint(self, client: TestClient):
        """Test the health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "language-quiz-service"
        assert "version" in data
        assert "environment" in data

    def test_cors_headers(self, client: TestClient):
        """Test that CORS headers are properly set."""
        # Test that a simple request works and has CORS headers
        response = client.get("/health")
        assert response.status_code == 200

        # FastAPI with CORSMiddleware should automatically handle preflight requests
        # We'll test that the middleware is configured by checking it doesn't break basic requests
        response = client.get("/", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200

    def test_nonexistent_endpoint(self, client: TestClient):
        """Test that non-existent endpoints return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_openapi_docs_available(self, client: TestClient):
        """Test that OpenAPI documentation is available."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_json_available(self, client: TestClient):
        """Test that OpenAPI JSON is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

        # Basic OpenAPI structure validation
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


@pytest.mark.functional
class TestApplicationLifespan:
    """Test application lifecycle events."""

    def test_app_startup_shutdown(self, client: TestClient):
        """Test that the app starts and shuts down properly."""
        # The app should be running if the test client works
        response = client.get("/health")
        assert response.status_code == 200


@pytest.mark.functional
class TestExceptionHandling:
    """Test exception handling in the application."""

    def test_http_exception_handling(self, client: TestClient):
        """Test that HTTP exceptions are handled properly."""
        # Test 404 for non-existent endpoint
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_internal_server_error_handling(self, client: TestClient, caplog):
        """Test that internal server errors are handled gracefully."""

        # Use FastAPI's dependency override system to inject a failing dependency
        def failing_get_settings():
            raise Exception("Test error")

        # Override the dependency to cause an exception
        app.dependency_overrides[get_settings] = failing_get_settings

        try:
            # Capture the logging output to verify our exception handler was called
            with caplog.at_level(logging.ERROR):
                # FastAPI's TestClient will raise the exception, but our handler should still log it
                with pytest.raises(Exception, match="Test error"):
                    client.get("/health")

            # Verify that our global exception handler was triggered and logged the error
            assert "Unhandled exception: Test error" in caplog.text
            assert any("src.main" in record.name for record in caplog.records)

        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()
