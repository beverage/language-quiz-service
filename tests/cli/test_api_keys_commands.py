"""Tests for API keys CLI commands."""

import json
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import asyncclick as click
import httpx
import pytest
from asyncclick.testing import CliRunner

from src.cli.api_keys.commands import create, list_keys, revoke, update
from src.cli.utils.http_client import make_api_request


class TestMakeAPIRequest:
    """Test the make_api_request function."""

    @patch("httpx.AsyncClient")
    async def test_make_api_request_success(self, mock_client_class):
        """Test successful API request."""
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
            base_url="http://localhost:8000",
            api_key="test_key",
            json_data={"test": "data"},
            params={"param": "value"},
        )

        # Verify the request was made correctly
        mock_client.request.assert_called_once_with(
            method="GET",
            url="http://localhost:8000/test",
            headers={
                "Authorization": "Bearer test_key",
                "Content-Type": "application/json",
            },
            json={"test": "data"},
            params={"param": "value"},
            timeout=30.0,
        )

        assert result == mock_response

    @patch("httpx.AsyncClient")
    async def test_make_api_request_http_error(self, mock_client_class):
        """Test API request with HTTP error."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Bad request"}

        mock_client = MagicMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client

        with pytest.raises(click.ClickException) as excinfo:
            await make_api_request("GET", "/test", "http://localhost:8000", "test_key")

        assert "API request failed: Bad request" in str(excinfo.value)

    @patch("httpx.AsyncClient")
    async def test_make_api_request_network_error(self, mock_client_class):
        """Test API request with network error."""
        mock_client = MagicMock()
        mock_client.request = AsyncMock(side_effect=httpx.RequestError("Network error"))
        mock_client_class.return_value.__aenter__.return_value = mock_client

        with pytest.raises(click.ClickException) as excinfo:
            await make_api_request("GET", "/test", "http://localhost:8000", "test_key")

        assert (
            "Network error connecting to http://localhost:8000/test: Network error"
            in str(excinfo.value)
        )

    @patch("httpx.AsyncClient")
    async def test_make_api_request_timeout(self, mock_client_class):
        """Test API request with timeout."""
        mock_client = MagicMock()
        mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client_class.return_value.__aenter__.return_value = mock_client

        with pytest.raises(click.ClickException) as excinfo:
            await make_api_request("GET", "/test", "http://localhost:8000", "test_key")

        assert "Network error connecting to http://localhost:8000/test: Timeout" in str(
            excinfo.value
        )


def make_context_runner():
    """Create a CLI runner with proper context setup for api-keys commands."""

    @click.group()
    @click.pass_context
    async def test_cli(ctx):
        """Test CLI group that sets up context like the real CLI."""
        ctx.ensure_object(dict)
        ctx.obj["service_url"] = "http://localhost:8000"
        ctx.obj["remote"] = False

    return test_cli


class TestCreateCommand:
    """Test the create API key command."""

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key")
    @pytest.mark.asyncio
    async def test_create_success(self, mock_get_api_key, mock_make_request):
        """Test successful API key creation."""
        mock_get_api_key.return_value = "auth_key"

        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "api_key": "test_key_cli_create_12345",
            "key_info": {
                "name": "test-key",
                "key_prefix": "test_key_cli_create_12345",
                "permissions_scope": ["read", "write"],
            },
        }
        mock_make_request.return_value = mock_response

        # Create test CLI with context
        test_cli = make_context_runner()
        test_cli.add_command(create)

        runner = CliRunner()
        result = await runner.invoke(
            test_cli,
            [
                "create",
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
        assert "test_key_cli_create_12345" in result.output

        # Verify API request was made correctly
        mock_make_request.assert_called_once_with(
            method="POST",
            endpoint="/api/v1/api-keys/",
            base_url="http://localhost:8000",
            api_key="auth_key",
            json_data={
                "name": "test-key",
                "description": "Test key",
                "permissions_scope": ["read", "write"],
                "rate_limit_rpm": 200,
            },
        )

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key")
    @pytest.mark.asyncio
    async def test_create_with_optional_params(
        self, mock_get_api_key, mock_make_request
    ):
        """Test API key creation with optional parameters."""
        mock_get_api_key.return_value = "auth_key"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "api_key": "test_key_cli_admin_12345",
            "key_info": {
                "name": "test-key",
                "key_prefix": "test_key_cli_admin_12345",
                "permissions_scope": ["admin"],
            },
        }
        mock_make_request.return_value = mock_response

        test_cli = make_context_runner()
        test_cli.add_command(create)

        runner = CliRunner()
        result = await runner.invoke(
            test_cli,
            [
                "create",
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
            endpoint="/api/v1/api-keys/",
            base_url="http://localhost:8000",
            api_key="auth_key",
            json_data={
                "name": "test-key",
                "client_name": "test-client",
                "allowed_ips": ["192.168.1.1", "192.168.1.2"],
                "permissions_scope": ["admin"],
                "rate_limit_rpm": 100,
            },
        )

    @patch("src.cli.api_keys.commands.get_api_key")
    @pytest.mark.asyncio
    async def test_create_no_auth_key_error(self, mock_get_api_key):
        """Test create command fails when no auth key is provided."""
        mock_get_api_key.side_effect = click.ClickException(
            "No API key found. Set SERVICE_API_KEY environment variable."
        )

        test_cli = make_context_runner()
        test_cli.add_command(create)

        runner = CliRunner()
        result = await runner.invoke(test_cli, ["create", "--name", "test-key"])

        assert result.exit_code != 0
        assert "No API key found" in result.output


class TestListKeysCommand:
    """Test the list_keys command."""

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key")
    @pytest.mark.asyncio
    async def test_list_keys_json_output(self, mock_get_api_key, mock_make_request):
        """Test listing keys with JSON output."""
        mock_get_api_key.return_value = "auth_key"

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "key_prefix": "test_key_cli_list_12345",
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

        test_cli = make_context_runner()
        test_cli.add_command(list_keys, name="list")

        runner = CliRunner()
        result = await runner.invoke(test_cli, ["list", "--json"])

        assert result.exit_code == 0

        # Verify JSON output
        output_data = json.loads(result.output)
        assert len(output_data) == 1
        assert output_data[0]["name"] == "test-key"

        mock_make_request.assert_called_once_with(
            method="GET",
            endpoint="/api/v1/api-keys/",
            base_url="http://localhost:8000",
            api_key="auth_key",
        )

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key")
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
                "key_prefix": "test_key_cli_table_12345",
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

        test_cli = make_context_runner()
        test_cli.add_command(list_keys, name="list")

        runner = CliRunner()
        result = await runner.invoke(test_cli, ["list"])

        assert result.exit_code == 0
        mock_console.print.assert_called_once()

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key")
    @pytest.mark.asyncio
    async def test_list_keys_empty_response(self, mock_get_api_key, mock_make_request):
        """Test listing keys when no keys exist."""
        mock_get_api_key.return_value = "auth_key"

        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_make_request.return_value = mock_response

        test_cli = make_context_runner()
        test_cli.add_command(list_keys, name="list")

        runner = CliRunner()
        result = await runner.invoke(test_cli, ["list"])

        assert result.exit_code == 0
        assert "No API keys found" in result.output


class TestUpdateCommand:
    """Test the update API key command."""

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key")
    @pytest.mark.asyncio
    async def test_update_success(self, mock_get_api_key, mock_make_request):
        """Test successful API key update."""
        mock_get_api_key.return_value = "auth_key"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "key_prefix": "sk_live_1234",
            "name": "Updated Key Name",
            "is_active": True,
            "permissions_scope": ["read", "write"],
            "rate_limit_rpm": 500,
            "allowed_ips": None,
        }
        mock_make_request.return_value = mock_response

        key_id = "123e4567-e89b-12d3-a456-426614174000"

        test_cli = make_context_runner()
        test_cli.add_command(update)

        runner = CliRunner()
        result = await runner.invoke(
            test_cli,
            ["update", key_id, "--name", "Updated Key Name", "--rate-limit", "500"],
        )

        assert result.exit_code == 0
        assert "API key updated successfully!" in result.output
        assert "Updated Key Name" in result.output

        mock_make_request.assert_called_once_with(
            method="PUT",
            endpoint=f"/api/v1/api-keys/{key_id}",
            base_url="http://localhost:8000",
            api_key="auth_key",
            json_data={
                "name": "Updated Key Name",
                "rate_limit_rpm": 500,
            },
        )

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key")
    @pytest.mark.asyncio
    async def test_update_permissions(self, mock_get_api_key, mock_make_request):
        """Test updating API key permissions."""
        mock_get_api_key.return_value = "auth_key"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "key_prefix": "sk_live_1234",
            "name": "Test Key",
            "is_active": True,
            "permissions_scope": ["read", "write", "admin"],
            "rate_limit_rpm": 100,
            "allowed_ips": None,
        }
        mock_make_request.return_value = mock_response

        key_id = "123e4567-e89b-12d3-a456-426614174000"

        test_cli = make_context_runner()
        test_cli.add_command(update)

        runner = CliRunner()
        result = await runner.invoke(
            test_cli,
            ["update", key_id, "--permissions", "read,write,admin"],
        )

        assert result.exit_code == 0
        mock_make_request.assert_called_once_with(
            method="PUT",
            endpoint=f"/api/v1/api-keys/{key_id}",
            base_url="http://localhost:8000",
            api_key="auth_key",
            json_data={
                "permissions_scope": ["read", "write", "admin"],
            },
        )

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key")
    @pytest.mark.asyncio
    async def test_update_deactivate(self, mock_get_api_key, mock_make_request):
        """Test deactivating an API key."""
        mock_get_api_key.return_value = "auth_key"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "key_prefix": "sk_live_1234",
            "name": "Test Key",
            "is_active": False,
            "permissions_scope": ["read"],
            "rate_limit_rpm": 100,
            "allowed_ips": None,
        }
        mock_make_request.return_value = mock_response

        key_id = "123e4567-e89b-12d3-a456-426614174000"

        test_cli = make_context_runner()
        test_cli.add_command(update)

        runner = CliRunner()
        result = await runner.invoke(test_cli, ["update", key_id, "--deactivate"])

        assert result.exit_code == 0
        assert "Active: No" in result.output
        mock_make_request.assert_called_once_with(
            method="PUT",
            endpoint=f"/api/v1/api-keys/{key_id}",
            base_url="http://localhost:8000",
            api_key="auth_key",
            json_data={"is_active": False},
        )

    @patch("src.cli.api_keys.commands.get_api_key")
    @pytest.mark.asyncio
    async def test_update_no_options_error(self, mock_get_api_key):
        """Test update command fails when no options are provided."""
        mock_get_api_key.return_value = "auth_key"

        key_id = "123e4567-e89b-12d3-a456-426614174000"

        test_cli = make_context_runner()
        test_cli.add_command(update)

        runner = CliRunner()
        result = await runner.invoke(test_cli, ["update", key_id])

        assert result.exit_code != 0
        assert "No update options provided" in result.output

    @patch("src.cli.api_keys.commands.get_api_key")
    @pytest.mark.asyncio
    async def test_update_invalid_uuid(self, mock_get_api_key):
        """Test update command with invalid UUID."""
        mock_get_api_key.return_value = "auth_key"

        test_cli = make_context_runner()
        test_cli.add_command(update)

        runner = CliRunner()
        result = await runner.invoke(
            test_cli, ["update", "invalid-uuid", "--name", "Test"]
        )

        assert result.exit_code != 0
        assert "Invalid UUID format" in result.output


class TestRevokeCommand:
    """Test the revoke API key command."""

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key")
    @pytest.mark.asyncio
    async def test_revoke_success(self, mock_get_api_key, mock_make_request):
        """Test successful API key revocation."""
        mock_get_api_key.return_value = "auth_key"

        mock_response = MagicMock()
        mock_make_request.return_value = mock_response

        key_id = "123e4567-e89b-12d3-a456-426614174000"

        test_cli = make_context_runner()
        test_cli.add_command(revoke)

        runner = CliRunner()
        result = await runner.invoke(test_cli, ["revoke", key_id])

        assert result.exit_code == 0
        assert f"API key {key_id} revoked successfully!" in result.output

        mock_make_request.assert_called_once_with(
            method="DELETE",
            endpoint=f"/api/v1/api-keys/{key_id}",
            base_url="http://localhost:8000",
            api_key="auth_key",
        )

    @patch("src.cli.api_keys.commands.get_api_key")
    @pytest.mark.asyncio
    async def test_revoke_invalid_uuid(self, mock_get_api_key):
        """Test revoke command with invalid UUID."""
        mock_get_api_key.return_value = "auth_key"

        test_cli = make_context_runner()
        test_cli.add_command(revoke)

        runner = CliRunner()
        result = await runner.invoke(test_cli, ["revoke", "invalid-uuid"])

        assert result.exit_code != 0
        assert "Invalid UUID format" in result.output

    @patch("src.cli.api_keys.commands.get_api_key")
    @pytest.mark.asyncio
    async def test_revoke_no_auth_key_error(self, mock_get_api_key):
        """Test revoke command fails when no auth key is provided."""
        mock_get_api_key.side_effect = click.ClickException(
            "No API key found. Set SERVICE_API_KEY environment variable."
        )

        key_id = "123e4567-e89b-12d3-a456-426614174000"

        test_cli = make_context_runner()
        test_cli.add_command(revoke)

        runner = CliRunner()
        result = await runner.invoke(test_cli, ["revoke", key_id])

        assert result.exit_code != 0
        assert "No API key found" in result.output


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key")
    @pytest.mark.asyncio
    async def test_commands_handle_api_errors(
        self, mock_get_api_key, mock_make_request
    ):
        """Test that commands handle API errors gracefully."""
        mock_get_api_key.return_value = "auth_key"
        mock_make_request.side_effect = click.ClickException("API Error")

        test_cli = make_context_runner()
        test_cli.add_command(create)
        test_cli.add_command(list_keys, name="list")
        test_cli.add_command(revoke)

        runner = CliRunner()

        # Test create command error handling
        result = await runner.invoke(test_cli, ["create", "--name", "test-key"])
        assert result.exit_code != 0
        assert "API Error" in result.output

        # Test list command error handling
        result = await runner.invoke(test_cli, ["list"])
        assert result.exit_code != 0
        assert "API Error" in result.output

        # Test revoke command error handling
        key_id = "123e4567-e89b-12d3-a456-426614174000"
        result = await runner.invoke(test_cli, ["revoke", key_id])
        assert result.exit_code != 0
        assert "API Error" in result.output

    @patch("src.cli.api_keys.commands.make_api_request")
    @patch("src.cli.api_keys.commands.get_api_key")
    @pytest.mark.asyncio
    async def test_commands_use_service_url_from_context(
        self, mock_get_api_key, mock_make_request
    ):
        """Test that commands get service_url from context."""
        mock_get_api_key.return_value = "auth_key"

        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_make_request.return_value = mock_response

        # Create CLI with custom service URL
        @click.group()
        @click.pass_context
        async def custom_cli(ctx):
            ctx.ensure_object(dict)
            ctx.obj["service_url"] = "https://custom.example.com"
            ctx.obj["remote"] = True

        custom_cli.add_command(list_keys, name="list")

        runner = CliRunner()
        result = await runner.invoke(custom_cli, ["list"])

        assert result.exit_code == 0

        # Verify the custom service URL was used
        mock_make_request.assert_called_once_with(
            method="GET",
            endpoint="/api/v1/api-keys/",
            base_url="https://custom.example.com",
            api_key="auth_key",
        )
