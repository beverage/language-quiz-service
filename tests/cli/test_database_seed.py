"""Tests for CLI database seed functionality."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from asyncclick.testing import CliRunner

from src.cli.database.seed import (
    SUPPORTED_TENSES,
    _enqueue_problem_generation,
    seed_database,
)
from src.schemas.problems import GrammarFocus
from src.schemas.verbs import Tense

# Filter expected warnings from async mocking
pytestmark = pytest.mark.filterwarnings("ignore::RuntimeWarning")


@pytest.mark.unit
class TestSupportedTenses:
    """Test cases for SUPPORTED_TENSES constant."""

    def test_supported_tenses_excludes_imperatif(self):
        """Verify IMPERATIF is excluded from supported tenses."""
        assert Tense.IMPERATIF not in SUPPORTED_TENSES

    def test_supported_tenses_has_seven_tenses(self):
        """Verify exactly 7 tenses are supported."""
        assert len(SUPPORTED_TENSES) == 7

    def test_supported_tenses_contains_expected_tenses(self):
        """Verify all expected tenses are included."""
        expected = [
            Tense.PRESENT,
            Tense.PASSE_COMPOSE,
            Tense.PLUS_QUE_PARFAIT,
            Tense.IMPARFAIT,
            Tense.FUTURE_SIMPLE,
            Tense.CONDITIONNEL,
            Tense.SUBJONCTIF,
        ]
        for tense in expected:
            assert tense in SUPPORTED_TENSES

    def test_future_simple_uses_correct_value(self):
        """Verify FUTURE_SIMPLE enum value is 'future_simple' (with 'e')."""
        assert Tense.FUTURE_SIMPLE.value == "future_simple"


@pytest.mark.unit
class TestEnqueueProblemGeneration:
    """Test cases for _enqueue_problem_generation helper."""

    @patch("src.cli.database.seed.make_api_request")
    async def test_enqueue_sends_correct_request_data(
        self, mock_make_api_request: MagicMock
    ):
        """Test that correct request data is sent to the API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "test-uuid-123"}
        mock_make_api_request.return_value = mock_response

        result = await _enqueue_problem_generation(
            service_url="http://localhost:8000",
            api_key="test-key",
            focus=GrammarFocus.CONJUGATION,
            tense=Tense.PRESENT,
            count=10,
        )

        assert result == {"request_id": "test-uuid-123"}

        # Verify API was called with correct parameters
        mock_make_api_request.assert_called_once()
        call_kwargs = mock_make_api_request.call_args.kwargs
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["endpoint"] == "/api/v1/problems/generate"
        assert call_kwargs["base_url"] == "http://localhost:8000"
        assert call_kwargs["api_key"] == "test-key"

        json_data = call_kwargs["json_data"]
        assert json_data["statement_count"] == 4
        assert json_data["count"] == 10
        assert json_data["focus"] == "conjugation"
        assert json_data["constraints"]["tenses_used"] == ["present"]

    @patch("src.cli.database.seed.make_api_request")
    async def test_enqueue_uses_future_simple_value(
        self, mock_make_api_request: MagicMock
    ):
        """Test that future_simple tense uses correct enum value."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "test-uuid-456"}
        mock_make_api_request.return_value = mock_response

        await _enqueue_problem_generation(
            service_url="http://localhost:8000",
            api_key="test-key",
            focus=GrammarFocus.PRONOUNS,
            tense=Tense.FUTURE_SIMPLE,
            count=5,
        )

        call_kwargs = mock_make_api_request.call_args.kwargs
        json_data = call_kwargs["json_data"]
        # Verify the value is "future_simple" (with 'e'), not "futur_simple"
        assert json_data["constraints"]["tenses_used"] == ["future_simple"]

    @patch("src.cli.database.seed.make_api_request")
    async def test_enqueue_with_pronouns_focus(self, mock_make_api_request: MagicMock):
        """Test that pronouns focus is passed correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "test-uuid-789"}
        mock_make_api_request.return_value = mock_response

        await _enqueue_problem_generation(
            service_url="http://localhost:8000",
            api_key="test-key",
            focus=GrammarFocus.PRONOUNS,
            tense=Tense.IMPARFAIT,
            count=20,
        )

        call_kwargs = mock_make_api_request.call_args.kwargs
        json_data = call_kwargs["json_data"]
        assert json_data["focus"] == "pronouns"
        assert json_data["count"] == 20


@pytest.mark.unit
class TestSeedDatabaseCommand:
    """Test cases for seed_database command using CliRunner."""

    @patch("src.cli.database.seed.make_api_request")
    @patch("src.cli.database.seed.get_api_key")
    @patch("src.cli.database.seed.get_service_url_from_flag")
    async def test_seed_enqueues_all_combinations(
        self,
        mock_get_service_url: MagicMock,
        mock_get_api_key: MagicMock,
        mock_make_api_request: MagicMock,
    ):
        """Test that seed enqueues requests for all 14 combinations."""
        mock_get_api_key.return_value = "test-key"
        mock_get_service_url.return_value = "http://localhost:8000"

        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "test-uuid"}
        mock_make_api_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(seed_database, ["--json"])

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)
        # Should have 14 requests (2 focuses × 7 tenses)
        assert len(output["requests"]) == 14
        assert output["summary"]["total_requests"] == 14

    @patch("src.cli.database.seed.make_api_request")
    @patch("src.cli.database.seed.get_api_key")
    @patch("src.cli.database.seed.get_service_url_from_flag")
    async def test_seed_calls_both_focuses(
        self,
        mock_get_service_url: MagicMock,
        mock_get_api_key: MagicMock,
        mock_make_api_request: MagicMock,
    ):
        """Test that seed calls API with both focus types."""
        mock_get_api_key.return_value = "test-key"
        mock_get_service_url.return_value = "http://localhost:8000"

        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "test-uuid"}
        mock_make_api_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(seed_database, ["--json"])

        assert result.exit_code == 0

        output = json.loads(result.output)

        # Extract all focus values
        focuses = {req["focus"] for req in output["requests"]}
        assert "conjugation" in focuses
        assert "pronouns" in focuses

    @patch("src.cli.database.seed.make_api_request")
    @patch("src.cli.database.seed.get_api_key")
    @patch("src.cli.database.seed.get_service_url_from_flag")
    async def test_seed_calls_all_supported_tenses(
        self,
        mock_get_service_url: MagicMock,
        mock_get_api_key: MagicMock,
        mock_make_api_request: MagicMock,
    ):
        """Test that seed calls API with all 7 supported tenses."""
        mock_get_api_key.return_value = "test-key"
        mock_get_service_url.return_value = "http://localhost:8000"

        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "test-uuid"}
        mock_make_api_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(seed_database, ["--json"])

        assert result.exit_code == 0

        output = json.loads(result.output)

        # Extract all tense values
        tenses = {req["tense"] for req in output["requests"]}

        # Verify all supported tenses were called
        expected_tenses = {t.value for t in SUPPORTED_TENSES}
        assert tenses == expected_tenses

        # Verify IMPERATIF was NOT called
        assert "imperatif" not in tenses

    @patch("src.cli.database.seed.make_api_request")
    @patch("src.cli.database.seed.get_api_key")
    @patch("src.cli.database.seed.get_service_url_from_flag")
    async def test_seed_respects_count_option(
        self,
        mock_get_service_url: MagicMock,
        mock_get_api_key: MagicMock,
        mock_make_api_request: MagicMock,
    ):
        """Test that custom count is passed to API calls."""
        mock_get_api_key.return_value = "test-key"
        mock_get_service_url.return_value = "http://localhost:8000"

        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "test-uuid"}
        mock_make_api_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(seed_database, ["--count", "50", "--json"])

        assert result.exit_code == 0

        output = json.loads(result.output)

        # Verify all requests used count=50
        for req in output["requests"]:
            assert req["count"] == 50

        # Verify summary calculation: 14 requests × 50 = 700 problems
        assert output["summary"]["total_problems_requested"] == 700

    @patch("src.cli.database.seed.make_api_request")
    @patch("src.cli.database.seed.get_api_key")
    @patch("src.cli.database.seed.get_service_url_from_flag")
    async def test_seed_json_output_format(
        self,
        mock_get_service_url: MagicMock,
        mock_get_api_key: MagicMock,
        mock_make_api_request: MagicMock,
    ):
        """Test that JSON output has correct structure."""
        mock_get_api_key.return_value = "test-key"
        mock_get_service_url.return_value = "http://localhost:8000"

        # Return different UUIDs for each call
        call_count = [0]

        def return_response(*args, **kwargs):
            call_count[0] += 1
            mock_response = MagicMock()
            mock_response.json.return_value = {"request_id": f"uuid-{call_count[0]}"}
            return mock_response

        mock_make_api_request.side_effect = return_response

        runner = CliRunner()
        result = await runner.invoke(seed_database, ["--json"])

        assert result.exit_code == 0

        output = json.loads(result.output)

        # Verify top-level structure
        assert "requests" in output
        assert "summary" in output
        assert len(output["requests"]) == 14

        # Verify request structure
        first_request = output["requests"][0]
        assert "request_id" in first_request
        assert "focus" in first_request
        assert "tense" in first_request
        assert "count" in first_request
        assert "timestamp" in first_request

        # Verify summary structure
        summary = output["summary"]
        assert summary["total_requests"] == 14
        assert summary["total_problems_requested"] == 140
        assert "by_focus" in summary
        assert "by_tense" in summary

    @patch("src.cli.database.seed.make_api_request")
    @patch("src.cli.database.seed.get_api_key")
    @patch("src.cli.database.seed.get_service_url_from_flag")
    async def test_seed_summary_by_focus_calculation(
        self,
        mock_get_service_url: MagicMock,
        mock_get_api_key: MagicMock,
        mock_make_api_request: MagicMock,
    ):
        """Test that by_focus summary is calculated correctly."""
        mock_get_api_key.return_value = "test-key"
        mock_get_service_url.return_value = "http://localhost:8000"

        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "test-uuid"}
        mock_make_api_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(seed_database, ["--json"])

        assert result.exit_code == 0

        output = json.loads(result.output)

        # 7 tenses × 10 count = 70 per focus
        assert output["summary"]["by_focus"]["conjugation"] == 70
        assert output["summary"]["by_focus"]["pronouns"] == 70

    @patch("src.cli.database.seed.make_api_request")
    @patch("src.cli.database.seed.get_api_key")
    @patch("src.cli.database.seed.get_service_url_from_flag")
    async def test_seed_summary_by_tense_calculation(
        self,
        mock_get_service_url: MagicMock,
        mock_get_api_key: MagicMock,
        mock_make_api_request: MagicMock,
    ):
        """Test that by_tense summary is calculated correctly."""
        mock_get_api_key.return_value = "test-key"
        mock_get_service_url.return_value = "http://localhost:8000"

        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "test-uuid"}
        mock_make_api_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(seed_database, ["--json"])

        assert result.exit_code == 0

        output = json.loads(result.output)
        by_tense = output["summary"]["by_tense"]

        # 2 focuses × 10 count = 20 per tense
        assert by_tense["present"] == 20
        assert by_tense["future_simple"] == 20
        assert len(by_tense) == 7

    @patch("src.cli.database.seed.make_api_request")
    @patch("src.cli.database.seed.get_api_key")
    @patch("src.cli.database.seed.get_service_url_from_flag")
    async def test_seed_handles_partial_failures(
        self,
        mock_get_service_url: MagicMock,
        mock_get_api_key: MagicMock,
        mock_make_api_request: MagicMock,
    ):
        """Test that partial failures are captured in errors array."""
        mock_get_api_key.return_value = "test-key"
        mock_get_service_url.return_value = "http://localhost:8000"

        # Fail on the 3rd call
        call_count = [0]

        def sometimes_fail(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 3:
                raise Exception("API error")
            mock_response = MagicMock()
            mock_response.json.return_value = {"request_id": f"uuid-{call_count[0]}"}
            return mock_response

        mock_make_api_request.side_effect = sometimes_fail

        runner = CliRunner()
        result = await runner.invoke(seed_database, ["--json"])

        # Exit code is 0 for JSON mode even with errors (errors in output)
        assert result.exit_code == 0

        output = json.loads(result.output)

        assert "errors" in output
        assert len(output["errors"]) == 1
        assert output["summary"]["failed_requests"] == 1
        assert output["summary"]["total_requests"] == 13

    @patch("src.cli.database.seed.get_api_key")
    @patch("src.cli.database.seed.get_service_url_from_flag")
    async def test_seed_handles_missing_api_key(
        self,
        mock_get_service_url: MagicMock,
        mock_get_api_key: MagicMock,
    ):
        """Test that missing API key is handled gracefully."""
        mock_get_service_url.return_value = "http://localhost:8000"
        mock_get_api_key.side_effect = Exception("API key not found")

        runner = CliRunner()
        result = await runner.invoke(seed_database, [])

        assert result.exit_code == 1
        assert "API key not found" in result.output

    @patch("src.cli.database.seed.make_api_request")
    @patch("src.cli.database.seed.get_api_key")
    @patch("src.cli.database.seed.get_service_url_from_flag")
    async def test_seed_display_mode_output(
        self,
        mock_get_service_url: MagicMock,
        mock_get_api_key: MagicMock,
        mock_make_api_request: MagicMock,
    ):
        """Test display mode shows progress and summary."""
        mock_get_api_key.return_value = "test-key"
        mock_get_service_url.return_value = "http://localhost:8000"

        mock_response = MagicMock()
        mock_response.json.return_value = {"request_id": "abcd1234-test-uuid"}
        mock_make_api_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(seed_database, [])

        assert result.exit_code == 0

        # Verify display output contains expected elements
        assert "🌱 Seeding database" in result.output
        assert "14 generation requests" in result.output
        assert "✅" in result.output
        assert "conjugation + present" in result.output
        assert "📊 Summary:" in result.output
        assert "14 requests enqueued" in result.output
        assert "140 problems requested" in result.output

    @patch("src.cli.database.seed.make_api_request")
    @patch("src.cli.database.seed.get_api_key")
    @patch("src.cli.database.seed.get_service_url_from_flag")
    async def test_seed_display_mode_shows_errors(
        self,
        mock_get_service_url: MagicMock,
        mock_get_api_key: MagicMock,
        mock_make_api_request: MagicMock,
    ):
        """Test display mode shows errors and exits with code 1."""
        mock_get_api_key.return_value = "test-key"
        mock_get_service_url.return_value = "http://localhost:8000"

        # All calls fail
        mock_make_api_request.side_effect = Exception("Connection refused")

        runner = CliRunner()
        result = await runner.invoke(seed_database, [])

        assert result.exit_code == 1
        assert "❌" in result.output
        assert "Connection refused" in result.output
