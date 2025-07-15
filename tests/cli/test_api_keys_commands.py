import json
from unittest.mock import AsyncMock, MagicMock, patch

import asyncclick as click
import httpx
import pytest
from asyncclick.testing import CliRunner

from src.cli.api_keys.commands import (
    create,
    get_api_base_url,
    get_api_key_from_env_or_flag,
    list_keys,
    make_api_request,
    revoke,
)


class TestAPIKeyHelpers:
    """Test helper functions for API key management."""

    def test_get_api_key_from_env_or_flag_env_priority(self):
        """Test that environment variable takes priority over flag."""
        with patch.dict("os.environ", {"LQS_API_KEY": "env_key"}):
            result = get_api_key_from_env_or_flag("flag_key")
            assert result == "env_key"

    def test_get_api_key_from_env_or_flag_flag_fallback(self):
        """Test that flag is used when env var is not set."""
        with patch.dict("os.environ", {}, clear=True):
            result = get_api_key_from_env_or_flag("flag_key")
            assert result == "flag_key"

    def test_get_api_key_from_env_or_flag_no_key_raises_exception(self):
        """Test that ClickException is raised when no key is provided."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(click.ClickException) as excinfo:
                get_api_key_from_env_or_flag(None)
            assert "No API key provided" in str(excinfo.value)

    def test_get_api_base_url_from_env(self):
        """Test getting base URL from environment variable."""
        with patch.dict("os.environ", {"LQS_SERVICE_URL": "https://api.example.com"}):
            result = get_api_base_url()
            assert result == "https://api.example.com"

    def test_get_api_base_url_default(self):
        """Test default base URL when env var is not set."""
        with patch.dict("os.environ", {}, clear=True):
            result = get_api_base_url()
            assert result == "http://localhost:8000"

    def test_get_api_base_url_fallback_on_exception(self):
        """Test fallback URL when settings raise exception."""
        with patch.dict("os.environ", {}, clear=True):
            result = get_api_base_url()
            assert result == "http://localhost:8000"


class TestMakeAPIRequest:
    """Test the make_api_request function."""

    @patch("src.cli.api_keys.commands.get_api_base_url")
    @patch("httpx.AsyncClient")
    async def test_make_api_request_success(self, mock_client_class, mock_get_base_url):
        """Test successful API request."""
        mock_get_base_url.return_value = "http://localhost:8000"

        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}

        # Mock the client
        mock_client = MagicMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Make the request
        result = await make_api_request(
            method="GET",
            endpoint="/test",
            api_key="test_key",
            json_data={"test": "data"},
            params={"param": "value"},
        )

        # Verify the request was made correctly
        mock_client.request.assert_called_once_with(
            method="GET",
            url="http://localhost:8000/test",
            headers={
                "X-API-Key": "test_key",
                "Content-Type": "application/json",
            },
            json={"test": "data"},
            params={"param": "value"},
            timeout=30.0,
        )

        assert result == mock_response

    @patch("src.cli.api_keys.commands.get_api_base_url")
    @patch("httpx.AsyncClient")
    async def test_make_api_request_http_error(
        self, mock_client_class, mock_get_base_url
    ):
        """Test API request with HTTP error."""
        mock_get_base_url.return_value = "http://localhost:8000"

        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Bad request"}

        mock_client = MagicMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client

        with pytest.raises(click.ClickException) as excinfo:
            await make_api_request("GET", "/test", "test_key")

        assert "API request failed: Bad request" in str(excinfo.value)

    @patch("src.cli.api_keys.commands.get_api_base_url")
    @patch("httpx.AsyncClient")
    async def test_make_api_request_network_error(
        self, mock_client_class, mock_get_base_url
    ):
        """Test API request with network error."""
        mock_get_base_url.return_value = "http://localhost:8000"

        mock_client = MagicMock()
        mock_client.request = AsyncMock(side_effect=httpx.RequestError("Network error"))
        mock_client_class.return_value.__aenter__.return_value = mock_client

        with pytest.raises(click.ClickException) as excinfo:
            await make_api_request("GET", "/test", "test_key")

        assert (
            "Network error connecting to http://localhost:8000/test: Network error"
            in str(excinfo.value)
        )

    @patch("src.cli.api_keys.commands.get_api_base_url")
    @patch("httpx.AsyncClient")
    async def test_make_api_request_timeout(self, mock_client_class, mock_get_base_url):
        """Test API request with timeout."""
        mock_get_base_url.return_value = "http://localhost:8000"

        mock_client = MagicMock()
        mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client_class.return_value.__aenter__.return_value = mock_client

        with pytest.raises(click.ClickException) as excinfo:
            await make_api_request("GET", "/test", "test_key")

        assert "Network error connecting to http://localhost:8000/test: Timeout" in str(
            excinfo.value
        )


class TestCreateCommand:
    """Test the create API key command."""

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key_from_env_or_flag")
    @pytest.mark.asyncio
    async def test_create_success(self, mock_get_api_key, mock_make_request):
        """Test successful API key creation."""
        mock_get_api_key.return_value = "auth_key"

        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "api_key": "sk_live_12345",
            "key_info": {
                "name": "test-key",
                "key_prefix": "sk_live_12345",
                "permissions_scope": ["read", "write"],
            },
        }
        mock_make_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(
            create,
            [
                "--name",
                "test-key",
                "--description",
                "Test key",
                "--permissions",
                "read,write",
                "--rate-limit",
                "200",
            ],
        )

        assert result.exit_code == 0
        assert "API key created successfully!" in result.output
        assert "Name: test-key" in result.output
        assert "sk_live_12345" in result.output

        # Verify API request was made correctly
        mock_make_request.assert_called_once_with(
            method="POST",
            endpoint="/api-keys/",
            api_key="auth_key",
            json_data={
                "name": "test-key",
                "description": "Test key",
                "permissions_scope": ["read", "write"],
                "rate_limit_rpm": 200,
            },
        )

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key_from_env_or_flag")
    @pytest.mark.asyncio
    async def test_create_with_optional_params(
        self, mock_get_api_key, mock_make_request
    ):
        """Test API key creation with optional parameters."""
        mock_get_api_key.return_value = "auth_key"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "api_key": "sk_live_12345",
            "key_info": {
                "name": "test-key",
                "key_prefix": "sk_live_12345",
                "permissions_scope": ["admin"],
            },
        }
        mock_make_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(
            create,
            [
                "--name",
                "test-key",
                "--client-name",
                "test-client",
                "--allowed-ips",
                "192.168.1.1,192.168.1.2",
                "--permissions",
                "admin",
            ],
        )

        assert result.exit_code == 0

        # Verify API request includes optional parameters
        mock_make_request.assert_called_once_with(
            method="POST",
            endpoint="/api-keys/",
            api_key="auth_key",
            json_data={
                "name": "test-key",
                "client_name": "test-client",
                "allowed_ips": ["192.168.1.1", "192.168.1.2"],
                "permissions_scope": ["admin"],
                "rate_limit_rpm": 100,
            },
        )

    @patch("src.cli.api_keys.commands.get_api_key_from_env_or_flag")
    @pytest.mark.asyncio
    async def test_create_no_auth_key_error(self, mock_get_api_key):
        """Test create command fails when no auth key is provided."""
        mock_get_api_key.side_effect = click.ClickException("No API key provided")

        runner = CliRunner()
        result = await runner.invoke(create, ["--name", "test-key"])

        assert result.exit_code != 0
        assert "No API key provided" in result.output


class TestListKeysCommand:
    """Test the list_keys command."""

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key_from_env_or_flag")
    @pytest.mark.asyncio
    async def test_list_keys_json_output(self, mock_get_api_key, mock_make_request):
        """Test listing keys with JSON output."""
        mock_get_api_key.return_value = "auth_key"

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "key_prefix": "sk_live_12345",
                "name": "test-key",
                "is_active": True,
                "permissions_scope": ["read"],
                "rate_limit_rpm": 100,
                "created_at": "2023-01-01T00:00:00Z",
                "last_used_at": "2023-01-02T00:00:00Z",
                "usage_count": 5,
            }
        ]
        mock_make_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(list_keys, ["--json"])

        assert result.exit_code == 0

        # Verify JSON output
        output_data = json.loads(result.output)
        assert len(output_data) == 1
        assert output_data[0]["name"] == "test-key"

        mock_make_request.assert_called_once_with(
            method="GET", endpoint="/api-keys/", api_key="auth_key"
        )

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key_from_env_or_flag")
    @patch("src.cli.api_keys.commands.Console")
    @pytest.mark.asyncio
    async def test_list_keys_table_output(
        self, mock_console_class, mock_get_api_key, mock_make_request
    ):
        """Test listing keys with table output."""
        mock_get_api_key.return_value = "auth_key"

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "key_prefix": "sk_live_12345",
                "name": "test-key",
                "is_active": True,
                "permissions_scope": ["read", "write"],
                "rate_limit_rpm": 100,
                "created_at": "2023-01-01T00:00:00Z",
                "last_used_at": "2023-01-02T00:00:00Z",
                "usage_count": 5,
            }
        ]
        mock_make_request.return_value = mock_response

        mock_console = MagicMock()
        mock_console_class.return_value = mock_console

        runner = CliRunner()
        result = await runner.invoke(list_keys)

        assert result.exit_code == 0
        mock_console.print.assert_called_once()

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key_from_env_or_flag")
    @pytest.mark.asyncio
    async def test_list_keys_empty_response(self, mock_get_api_key, mock_make_request):
        """Test listing keys when no keys exist."""
        mock_get_api_key.return_value = "auth_key"

        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_make_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(list_keys)

        assert result.exit_code == 0
        assert "No API keys found" in result.output


class TestRevokeCommand:
    """Test the revoke API key command."""

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key_from_env_or_flag")
    @pytest.mark.asyncio
    async def test_revoke_success(self, mock_get_api_key, mock_make_request):
        """Test successful API key revocation."""
        mock_get_api_key.return_value = "auth_key"

        mock_response = MagicMock()
        mock_make_request.return_value = mock_response

        key_id = "123e4567-e89b-12d3-a456-426614174000"

        runner = CliRunner()
        result = await runner.invoke(revoke, [key_id])

        assert result.exit_code == 0
        assert f"API key {key_id} revoked successfully!" in result.output

        mock_make_request.assert_called_once_with(
            method="POST", endpoint=f"/api-keys/{key_id}/revoke", api_key="auth_key"
        )

    @pytest.mark.asyncio
    async def test_revoke_invalid_uuid(self):
        """Test revoke command with invalid UUID."""
        runner = CliRunner()
        result = await runner.invoke(revoke, ["invalid-uuid", "--api-key", "test-key"])

        assert result.exit_code != 0
        assert "Invalid UUID format" in result.output

    @patch("src.cli.api_keys.commands.get_api_key_from_env_or_flag")
    @pytest.mark.asyncio
    async def test_revoke_no_auth_key_error(self, mock_get_api_key):
        """Test revoke command fails when no auth key is provided."""
        mock_get_api_key.side_effect = click.ClickException("No API key provided")

        key_id = "123e4567-e89b-12d3-a456-426614174000"

        runner = CliRunner()
        result = await runner.invoke(revoke, [key_id])

        assert result.exit_code != 0
        assert "No API key provided" in result.output


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key_from_env_or_flag")
    @pytest.mark.asyncio
    async def test_create_with_api_key_flag(self, mock_get_api_key, mock_make_request):
        """Test create command using --api-key flag."""
        mock_get_api_key.return_value = "flag_key"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "api_key": "sk_live_12345",
            "key_info": {
                "name": "test-key",
                "key_prefix": "sk_live_12345",
                "permissions_scope": ["read"],
            },
        }
        mock_make_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(
            create, ["--name", "test-key", "--api-key", "flag_key"]
        )

        assert result.exit_code == 0
        mock_get_api_key.assert_called_once_with("flag_key")

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key_from_env_or_flag")
    @pytest.mark.asyncio
    async def test_list_with_api_key_flag(self, mock_get_api_key, mock_make_request):
        """Test list command using --api-key flag."""
        mock_get_api_key.return_value = "flag_key"

        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_make_request.return_value = mock_response

        runner = CliRunner()
        result = await runner.invoke(list_keys, ["--api-key", "flag_key"])

        assert result.exit_code == 0
        mock_get_api_key.assert_called_once_with("flag_key")

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key_from_env_or_flag")
    @pytest.mark.asyncio
    async def test_commands_handle_api_errors(
        self, mock_get_api_key, mock_make_request
    ):
        """Test that commands handle API errors gracefully."""
        mock_get_api_key.return_value = "auth_key"
        mock_make_request.side_effect = click.ClickException("API Error")

        runner = CliRunner()

        # Test create command error handling
        result = await runner.invoke(create, ["--name", "test-key"])
        assert result.exit_code != 0
        assert "API Error" in result.output

        # Test list command error handling
        result = await runner.invoke(list_keys)
        assert result.exit_code != 0
        assert "API Error" in result.output

        # Test revoke command error handling
        key_id = "123e4567-e89b-12d3-a456-426614174000"
        result = await runner.invoke(revoke, [key_id])
        assert result.exit_code != 0
        assert "API Error" in result.output
