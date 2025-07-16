"""Tests for the API key authentication middleware."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.auth import ApiKeyAuthMiddleware


class TestApiKeyAuthMiddleware:
    """Test suite for API key authentication middleware."""

    @pytest.fixture
    def test_app(self):
        """Create test FastAPI app with auth middleware."""
        app = FastAPI()

        # Add the auth middleware
        app.add_middleware(ApiKeyAuthMiddleware)

        @app.get("/health")
        def health():
            return {"status": "ok"}

        return app

    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return TestClient(test_app)

    def test_health_endpoint_exempt(self, client):
        """Health endpoint should be exempt from authentication."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
