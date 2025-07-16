"""Clean API contract tests for verbs endpoints.

These tests focus on HTTP request/response behavior, parameter handling,
and API contract validation without complex dependency injection.
"""

from contextlib import contextmanager
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.schemas.verbs import (
    VerbCreate,
    VerbWithConjugations,
)

# Import fixtures from verbs domain
from tests.verbs.fixtures import generate_random_verb_data, sample_verb


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def admin_headers():
    """Headers with admin test API key."""
    return {
        "X-API-Key": "sk_live_adm1234567890123456789012345678901234567890123456789012345678901234"
    }


@pytest.fixture
def write_headers():
    """Headers with read/write test API key."""
    return {
        "X-API-Key": "sk_live_wrt1234567890123456789012345678901234567890123456789012345678901234"
    }


@pytest.fixture
def read_headers():
    """Headers with read-only test API key."""
    return {
        "X-API-Key": "sk_live_red1234567890123456789012345678901234567890123456789012345678901234"
    }


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
        assert "not found" in response.json()["detail"].lower()

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
        assert "not found" in response.json()["detail"].lower()

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
        assert "permission required" in response.json()["detail"].lower()

    @pytest.mark.parametrize(
        "infinitive, expected_status, expected_detail_part",
        [
            ("chanter", 201, "chanter"),  # Verb that should not exist yet
            (
                "parler",
                409,
                "already exists",
            ),  # Verb that already exists in test data
            (
                "invalidverb123",
                400,
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
        # Mock the LLM client to avoid actual API calls during tests
        with patch("src.clients.openai_client.OpenAIClient") as mock_openai_client:
            mock_llm = AsyncMock()
            mock_openai_client.return_value = mock_llm

            # Simulate a successful LLM response for valid verbs
            if "invalid" not in infinitive:
                mock_llm.generate_verb.return_value = {
                    "infinitive": infinitive,
                    "auxiliary": "avoir",
                    "reflexive": False,
                    "translation_eng": f"to {infinitive}",
                    "past_participle": f"{infinitive}e",
                    "present_participle": f"{infinitive}ant",
                    "classification": "first_group",
                    "is_irregular": False,
                    "can_have_cod": True,
                    "can_have_coi": False,
                    "conjugations": {
                        "present": {
                            "first_person_singular": "chante",
                            "second_person_singular": "chantes",
                            "third_person_singular": "chante",
                            "first_person_plural": "chantons",
                            "second_person_plural": "chantez",
                            "third_person_plural": "chantent",
                        }
                    },
                }
            else:
                # Simulate the service raising a ContentGenerationError for invalid verbs
                mock_llm.generate_verb.side_effect = Exception(
                    f"'{infinitive}' is not a valid french verb"
                )

            request_body = {"infinitive": infinitive, "target_language_code": "eng"}
            response = client.post(
                f"{self.VERBS_PREFIX}/download", json=request_body, headers=write_headers
            )

            assert response.status_code == expected_status
            if expected_status != 201:
                assert (
                    expected_detail_part in response.json()["detail"].lower()
                ), f"Expected '{expected_detail_part}' in '{response.json()['detail']}'"
            else:
                assert response.json()["infinitive"] == infinitive
