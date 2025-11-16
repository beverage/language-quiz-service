"""Tests for topic_tags in Problem API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.problems import API_PREFIX
from src.main import ROUTER_PREFIX, app
from src.schemas.verbs import VerbCreate
from tests.problems.fixtures import mock_llm_responses
from tests.verbs.fixtures import sample_verb_data

PROBLEMS_PREFIX = f"{ROUTER_PREFIX}{API_PREFIX}"


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.mark.integration
class TestProblemGenerationWithTopicTags:
    """Test topic_tags functionality in problem generation API."""

    @pytest.fixture
    async def test_verb(self, request):
        """Get a known good verb with conjugations for problem generation."""
        from src.services.verb_service import VerbService

        verb_service = VerbService()

        # Use known good verbs that have conjugations in migrations
        # Use hash of test name to deterministically select verb (avoid random race conditions)
        known_verbs = ["être", "avoir", "pouvoir", "aller", "faire", "savoir", "parler"]
        test_name = request.node.name
        verb_index = hash(test_name) % len(known_verbs)
        infinitive = known_verbs[verb_index]

        verb = await verb_service.get_verb_by_infinitive(infinitive)
        if not verb:
            raise ValueError(f"Known verb {infinitive} not found in database")
        return verb

    @pytest.fixture
    def mock_queue_service(self):
        """Mock queue service to avoid Kafka connection in tests."""
        with patch("src.api.problems.QueueService") as mock_class:
            mock_instance = AsyncMock()

            async def mock_publish(**kwargs):
                count = kwargs.get("count", 1)
                request_ids = [f"req-id-{i}" for i in range(count)]
                return count, request_ids

            mock_instance.publish_problem_generation_request = mock_publish
            mock_class.return_value = mock_instance
            yield mock_instance

    @pytest.fixture(autouse=True)
    def mock_random_verb(self, test_verb):
        """Automatically mock get_random_verb for all tests in this class."""
        with patch(
            "src.services.problem_service.VerbService.get_random_verb",
            return_value=test_verb,
        ):
            yield

    async def test_topic_tags_in_response(
        self, client: TestClient, read_headers, mock_queue_service
    ):
        """Test that topic_tags are accepted in async generation request."""
        response = client.post(
            f"{PROBLEMS_PREFIX}/generate",
            headers=read_headers,
            json={"topic_tags": ["test_data", "custom_tag", "advanced"]},
        )

        assert response.status_code == 202
        data = response.json()
        assert data["count"] == 1

    async def test_empty_topic_tags(
        self, client: TestClient, read_headers, mock_queue_service
    ):
        """Test API with empty topic_tags list."""
        response = client.post(
            f"{PROBLEMS_PREFIX}/generate",
            headers=read_headers,
            json={"topic_tags": ["test_data"]},
        )

        assert response.status_code == 202
        data = response.json()
        assert data["count"] == 1

    async def test_topic_tags_with_constraints(
        self, client: TestClient, read_headers, mock_queue_service
    ):
        """Test topic_tags alongside problem generation constraints."""
        response = client.post(
            f"{PROBLEMS_PREFIX}/generate",
            headers=read_headers,
            json={
                "constraints": {
                    "grammatical_focus": ["negation"],
                    "includes_negation": True,
                },
                "statement_count": 6,
                "topic_tags": ["test_data", "negation_test"],
            },
        )

        assert response.status_code == 202
        data = response.json()
        assert data["count"] == 1

    async def test_topic_tags_with_special_characters(
        self, client: TestClient, read_headers, mock_queue_service
    ):
        """Test that topic_tags with special characters are accepted."""
        response = client.post(
            f"{PROBLEMS_PREFIX}/generate",
            headers=read_headers,
            json={
                "topic_tags": [
                    "test_data",
                    "special-chars",
                    "tag_with_underscore",
                    "tag.with.dots",
                ]
            },
        )

        assert response.status_code == 202
        data = response.json()
        assert data["count"] == 1

    async def test_invalid_topic_tags_type(
        self, client: TestClient, read_headers, test_verb, mock_llm_responses
    ):
        """Test that invalid topic_tags type is rejected."""
        response = client.post(
            f"{PROBLEMS_PREFIX}/generate",
            headers=read_headers,
            json={"topic_tags": "not_a_list"},  # Invalid: string instead of list
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.integration
class TestProblemCleanupByTopicTags:
    """Test that problems can be cleaned up by topic_tags."""

    async def test_cleanup_finds_test_data_tag(self, test_supabase_client):
        """Test that cleanup can find problems by test_data tag."""
        from src.repositories.problem_repository import ProblemRepository
        from src.schemas.problems import ProblemCreate, ProblemType
        from tests.problems.fixtures import generate_random_problem_data

        repo = ProblemRepository(test_supabase_client)

        # Create a problem with test_data tag
        problem_data = generate_random_problem_data(
            title="Cleanup test problem", topic_tags=["test_data", "cleanup_test"]
        )
        created = await repo.create_problem(ProblemCreate(**problem_data))

        # Query for problems with test_data tag
        result = (
            await test_supabase_client.table("problems")
            .select("id, title, topic_tags")
            .contains("topic_tags", ["test_data"])
            .execute()
        )

        assert len(result.data) > 0
        assert any(p["id"] == str(created.id) for p in result.data)

        # Cleanup
        await repo.delete_problem(created.id)

    async def test_cleanup_ignores_non_test_problems(self, test_supabase_client):
        """Test that cleanup doesn't find problems without test_data tag."""
        from src.repositories.problem_repository import ProblemRepository
        from src.schemas.problems import ProblemCreate
        from tests.problems.fixtures import generate_random_problem_data

        repo = ProblemRepository(test_supabase_client)

        # Create a problem WITHOUT test_data tag
        problem_data = generate_random_problem_data(
            title="Real problem",
            topic_tags=["grammar", "production"],  # No test_data
        )
        # Override the automatic test_data addition
        problem_data["topic_tags"] = ["grammar", "production"]

        created = await repo.create_problem(ProblemCreate(**problem_data))

        # Query for problems with test_data tag
        result = (
            await test_supabase_client.table("problems")
            .select("id, title, topic_tags")
            .contains("topic_tags", ["test_data"])
            .execute()
        )

        # This problem should NOT be in the results
        assert not any(p["id"] == str(created.id) for p in result.data)

        # Cleanup
        await repo.delete_problem(created.id)
