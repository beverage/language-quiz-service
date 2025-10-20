"""API tests for verb endpoints."""

import json
from unittest.mock import AsyncMock, patch
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
        "infinitive, expected_status, expected_detail_part",
        [
            (
                "chanter_test_RANDOM",
                201,
                "chanter",
            ),  # Unique verb that should not exist - RANDOM will be replaced at runtime
            (
                "parler",
                409,
                "already exists",
            ),  # Verb that already exists in test data
            (
                "invalidverb123",
                503,
                "is not a valid french verb",
            ),  # Invalid verb format
        ],
    )
    def test_download_verb_scenarios(
        self,
        client: TestClient,
        write_headers,
        infinitive,
        expected_status,
        expected_detail_part,
    ):
        """Test various scenarios for the download verb endpoint."""
        # Replace RANDOM placeholder with actual UUID at runtime
        if "RANDOM" in infinitive:
            infinitive = infinitive.replace("RANDOM", uuid4().hex[:8])

        # Only mock the LLM client to avoid actual API calls
        with patch("src.services.verb_service.OpenAIClient") as mock_openai_client:
            mock_llm_instance = mock_openai_client.return_value
            mock_llm_instance.handle_request = AsyncMock()

            # Simulate a successful LLM response for valid verbs
            if "invalid" not in infinitive:
                # Mock main verb response
                mock_llm_instance.handle_request.side_effect = [
                    json.dumps(
                        {
                            "infinitive": infinitive,
                            "auxiliary": "avoir",
                            "reflexive": False,
                            "translation": f"to {infinitive}",
                            "past_participle": f"{infinitive}e",
                            "present_participle": f"{infinitive}ant",
                            "classification": "first_group",
                            "is_irregular": False,
                            "target_language_code": "eng",
                            "tenses": [
                                {
                                    "tense": "present",
                                    "infinitive": infinitive,
                                    "auxiliary": "avoir",
                                    "first_person_singular": "chante",
                                    "second_person_singular": "chantes",
                                    "third_person_singular": "chante",
                                    "first_person_plural": "chantons",
                                    "second_person_plural": "chantez",
                                    "third_person_plural": "chantent",
                                }
                            ],
                        }
                    ),
                    # Mock objects response (COD/COI)
                    json.dumps(
                        {
                            "can_have_cod": True,
                            "can_have_coi": False,
                        }
                    ),
                ]
            else:
                # Simulate the LLM raising an error for invalid verbs
                mock_llm_instance.handle_request.side_effect = ContentGenerationError(
                    content_type="verb",
                    message=f"'{infinitive}' is not a valid french verb",
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
