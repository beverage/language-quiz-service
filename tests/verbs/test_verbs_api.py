"""API tests for verb endpoints."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.core.exceptions import ContentGenerationError
from src.main import app
from src.schemas.verbs import (
    Verb,
    VerbCreate,
    VerbWithConjugations,
)
from tests.conftest import mock_llm_response

# Import fixtures from verbs domain
from tests.verbs.fixtures import (
    generate_random_verb_data,
    generate_sample_verb_data,
    sample_verb,
)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


# Note: admin_headers, write_headers, and read_headers are now provided
# by tests/conftest.py with dynamically generated test keys


@pytest.mark.integration
class TestVerbsAPIIntegration:
    """Test verbs API endpoints with real database integration."""

    VERBS_PREFIX = "/api/v1/verbs"

    def test_get_verb_by_infinitive_success(self, client: TestClient, read_headers):
        """Test retrieving an existing verb by its infinitive."""
        # Assuming 'parler' exists in the test database
        response = client.get(f"{self.VERBS_PREFIX}/parler", headers=read_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["infinitive"] == "parler"
        assert "id" in data

    def test_get_verb_by_infinitive_not_found(self, client: TestClient, read_headers):
        """Test retrieving a non-existent verb."""
        response = client.get(
            f"{self.VERBS_PREFIX}/nonexistentverb", headers=read_headers
        )
        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()

    def test_get_verb_conjugations_success(self, client: TestClient, read_headers):
        """Test retrieving conjugations for an existing verb."""
        response = client.get(
            f"{self.VERBS_PREFIX}/parler/conjugations", headers=read_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["infinitive"] == "parler"
        assert "conjugations" in data
        assert isinstance(data["conjugations"], list)

    def test_get_verb_conjugations_not_found(self, client: TestClient, read_headers):
        """Test retrieving conjugations for a non-existent verb."""
        response = client.get(
            f"{self.VERBS_PREFIX}/nonexistentverb/conjugations", headers=read_headers
        )
        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()

    def test_get_random_verb_success(self, client: TestClient, read_headers):
        """Test retrieving a random verb."""
        response = client.get(f"{self.VERBS_PREFIX}/random", headers=read_headers)
        assert response.status_code == 200
        data = response.json()
        assert "infinitive" in data
        assert "id" in data

    def test_download_verb_permission_denied(self, client: TestClient, read_headers):
        """Test that downloading a verb requires write permission."""
        request_body = {"infinitive": "tester", "target_language_code": "eng"}
        response = client.post(
            f"{self.VERBS_PREFIX}/download", json=request_body, headers=read_headers
        )
        assert response.status_code == 403
        assert "permission required" in response.json()["message"].lower()

    @pytest.mark.parametrize(
        "infinitive, setup_verb, expected_status, expected_detail_part",
        [
            (
                "parler",  # Verb that exists in test data
                False,  # Don't need to create it
                200,  # Now returns 200 for successful conjugation download
                "parler",
            ),
            (
                "nonexistent_verb",  # Verb that doesn't exist
                False,
                404,  # Should return 404 since verb doesn't exist
                "not found",
            ),
        ],
    )
    def test_download_verb_scenarios(
        self,
        client: TestClient,
        write_headers,
        infinitive,
        setup_verb,
        expected_status,
        expected_detail_part,
    ):
        """Test various scenarios for the conjugation download endpoint.

        Note: This endpoint now ONLY downloads conjugations for existing verbs.
        Verbs must be added via database migrations first.
        """
        # Only mock the LLM client to avoid actual API calls
        with patch("src.services.verb_service.get_client") as mock_get_client:
            mock_llm_instance = MagicMock()
            mock_llm_instance.handle_request = AsyncMock()
            mock_get_client.return_value = mock_llm_instance

            # Mock conjugation response (returns LLMResponse with JSON array)
            if expected_status == 200:
                mock_llm_instance.handle_request.return_value = mock_llm_response(
                    json.dumps(
                        [
                            {
                                "tense": "present",
                                "infinitive": infinitive,
                                "auxiliary": "avoir",
                                "reflexive": False,
                                "first_person_singular": "parle",
                                "second_person_singular": "parles",
                                "third_person_singular": "parle",
                                "first_person_plural": "parlons",
                                "second_person_plural": "parlez",
                                "third_person_plural": "parlent",
                            }
                        ]
                    )
                )

            request_body = {
                "infinitive": infinitive,
                "target_language_code": "eng",
            }
            response = client.post(
                f"{self.VERBS_PREFIX}/download",
                json=request_body,
                headers=write_headers,
            )

            assert response.status_code == expected_status
            assert expected_detail_part in response.text


@pytest.mark.integration
class TestVerbsAPIRealIntegration:
    """Test verbs API endpoints with real database integration."""

    VERBS_PREFIX = "/api/v1/verbs"

    def test_get_verb_by_infinitive_success(self, client: TestClient, read_headers):
        """Test retrieving an existing verb by its infinitive."""
        # Assuming 'parler' exists in the test database
        response = client.get(f"{self.VERBS_PREFIX}/parler", headers=read_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["infinitive"] == "parler"
        assert "id" in data

    def test_get_verb_by_infinitive_not_found(self, client: TestClient, read_headers):
        """Test retrieving a non-existent verb."""
        response = client.get(
            f"{self.VERBS_PREFIX}/nonexistentverb", headers=read_headers
        )
        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()

    def test_get_verb_conjugations_success(self, client: TestClient, read_headers):
        """Test retrieving conjugations for an existing verb."""
        response = client.get(
            f"{self.VERBS_PREFIX}/parler/conjugations", headers=read_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["infinitive"] == "parler"
        assert "conjugations" in data
        assert isinstance(data["conjugations"], list)

    def test_get_verb_conjugations_not_found(self, client: TestClient, read_headers):
        """Test retrieving conjugations for a non-existent verb."""
        response = client.get(
            f"{self.VERBS_PREFIX}/nonexistentverb/conjugations", headers=read_headers
        )
        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()

    def test_get_random_verb_success(self, client: TestClient, read_headers):
        """Test retrieving a random verb."""
        response = client.get(f"{self.VERBS_PREFIX}/random", headers=read_headers)
        assert response.status_code == 200
        data = response.json()
        assert "infinitive" in data
        assert "id" in data

    def test_download_verb_permission_denied(self, client: TestClient, read_headers):
        """Test that downloading a verb requires write permission."""
        request_body = {"infinitive": "tester", "target_language_code": "eng"}
        response = client.post(
            f"{self.VERBS_PREFIX}/download", json=request_body, headers=read_headers
        )
        assert response.status_code == 403
        assert "permission required" in response.json()["message"].lower()
