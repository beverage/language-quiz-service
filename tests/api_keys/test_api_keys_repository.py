"""Unit tests for the API keys repository."""

import uuid
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timezone

import pytest

from src.repositories.api_keys_repository import ApiKeyRepository
from src.schemas.api_keys import ApiKey, ApiKeyCreate, ApiKeyUpdate, ApiKeyStats


@pytest.fixture
def mock_supabase_client() -> MagicMock:
    """Provides a mock Supabase client for testing."""
    return MagicMock()


@pytest.fixture
def sample_api_key_create():
    """Sample API key creation data."""
    return ApiKeyCreate(
        name="Test API Key",
        description="A test API key for unit testing",
        client_name="Test Client",
        permissions_scope=["read", "write"],
        rate_limit_rpm=100,
        allowed_ips=["192.168.1.0/24"],
    )


@pytest.fixture
def sample_api_key():
    """Sample complete API key data."""
    return ApiKey(
        id=uuid.uuid4(),
        key_hash="$2b$12$example_hash_here",
        key_prefix="sk_live_abcd1234",
        name="Test API Key",
        description="A test API key",
        client_name="Test Client",
        is_active=True,
        permissions_scope=["read", "write"],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_used_at=None,
        usage_count=0,
        rate_limit_rpm=100,
        allowed_ips=["192.168.1.0/24"],
    )


@pytest.mark.unit
@pytest.mark.asyncio
class TestApiKeyRepository:
    """Test cases for the ApiKeyRepository."""

    @pytest.fixture
    def repository(self, mock_supabase_client: MagicMock) -> ApiKeyRepository:
        """Fixture to create an ApiKeyRepository with a mock client."""
        return ApiKeyRepository(client=mock_supabase_client)

    async def test_create_api_key_success(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
        sample_api_key_create: ApiKeyCreate,
        sample_api_key: ApiKey,
    ):
        """Test successful creation of an API key."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.data = [sample_api_key.model_dump(mode="json")]

        # Setup mock chain
        insert_mock = MagicMock()
        insert_mock.execute = AsyncMock(return_value=mock_response)
        table_mock = MagicMock()
        table_mock.insert.return_value = insert_mock
        mock_supabase_client.table.return_value = table_mock

        # Execute
        result = await repository.create_api_key(
            sample_api_key_create, "test_hash", "sk_live_test"
        )

        # Verify
        assert isinstance(result, ApiKey)
        assert result.name == sample_api_key.name
        mock_supabase_client.table.assert_called_once_with("api_keys")
        table_mock.insert.assert_called_once()

    async def test_create_api_key_failure(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
        sample_api_key_create: ApiKeyCreate,
    ):
        """Test API key creation failure."""
        # Setup mock response with no data
        mock_response = MagicMock()
        mock_response.data = []

        # Setup mock chain
        insert_mock = MagicMock()
        insert_mock.execute = AsyncMock(return_value=mock_response)
        table_mock = MagicMock()
        table_mock.insert.return_value = insert_mock
        mock_supabase_client.table.return_value = table_mock

        # Execute and verify exception
        with pytest.raises(Exception, match="Failed to create API key"):
            await repository.create_api_key(
                sample_api_key_create, "test_hash", "sk_live_test"
            )

    async def test_get_api_key_found(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
        sample_api_key: ApiKey,
    ):
        """Test getting an API key by ID when it exists."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.data = [sample_api_key.model_dump(mode="json")]

        # Setup mock chain
        execute_mock = AsyncMock(return_value=mock_response)
        eq_mock = MagicMock()
        eq_mock.execute = execute_mock
        select_mock = MagicMock()
        select_mock.eq.return_value = eq_mock
        table_mock = MagicMock()
        table_mock.select.return_value = select_mock
        mock_supabase_client.table.return_value = table_mock

        # Execute
        result = await repository.get_api_key(sample_api_key.id)

        # Verify
        assert isinstance(result, ApiKey)
        assert result.id == sample_api_key.id
        mock_supabase_client.table.assert_called_once_with("api_keys")
        table_mock.select.assert_called_once_with("*")
        select_mock.eq.assert_called_once_with("id", str(sample_api_key.id))

    async def test_get_api_key_not_found(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
    ):
        """Test getting an API key by ID when it doesn't exist."""
        # Setup mock response with no data
        mock_response = MagicMock()
        mock_response.data = []

        # Setup mock chain
        execute_mock = AsyncMock(return_value=mock_response)
        eq_mock = MagicMock()
        eq_mock.execute = execute_mock
        select_mock = MagicMock()
        select_mock.eq.return_value = eq_mock
        table_mock = MagicMock()
        table_mock.select.return_value = select_mock
        mock_supabase_client.table.return_value = table_mock

        # Execute
        result = await repository.get_api_key(uuid.uuid4())

        # Verify
        assert result is None

    async def test_get_api_key_by_hash_found_active(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
        sample_api_key: ApiKey,
    ):
        """Test getting an active API key by hash."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.data = [sample_api_key.model_dump(mode="json")]

        # Setup mock chain that matches the actual call pattern
        execute_mock = AsyncMock(return_value=mock_response)
        eq2_mock = MagicMock()
        eq2_mock.execute = execute_mock
        eq1_mock = MagicMock()
        eq1_mock.eq.return_value = eq2_mock
        select_mock = MagicMock()
        select_mock.eq.return_value = eq1_mock
        table_mock = MagicMock()
        table_mock.select.return_value = select_mock
        mock_supabase_client.table.return_value = table_mock

        # Execute
        result = await repository.get_api_key_by_hash("test_hash")

        # Verify
        assert isinstance(result, ApiKey)
        assert result.id == sample_api_key.id
        # Verify the calls were made correctly (order is important)
        select_mock.eq.assert_called_once_with("key_hash", "test_hash")
        eq1_mock.eq.assert_called_once_with("is_active", True)

    async def test_get_api_key_by_hash_not_found(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
    ):
        """Test getting an API key by hash when not found."""
        # Setup mock response with no data
        mock_response = MagicMock()
        mock_response.data = []

        # Setup mock chain
        execute_mock = AsyncMock(return_value=mock_response)
        eq2_mock = MagicMock()
        eq2_mock.execute = execute_mock
        eq1_mock = MagicMock()
        eq1_mock.eq.return_value = eq2_mock
        select_mock = MagicMock()
        select_mock.eq.return_value = eq1_mock
        table_mock = MagicMock()
        table_mock.select.return_value = select_mock
        mock_supabase_client.table.return_value = table_mock

        # Execute
        result = await repository.get_api_key_by_hash("nonexistent_hash")

        # Verify
        assert result is None

    async def test_get_all_api_keys_active_only(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
        sample_api_key: ApiKey,
    ):
        """Test getting all active API keys."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.data = [sample_api_key.model_dump(mode="json")]

        # Setup mock chain that matches the actual repository call pattern
        execute_mock = AsyncMock(return_value=mock_response)
        order_mock = MagicMock()
        order_mock.execute = execute_mock
        eq_mock = MagicMock()
        eq_mock.order.return_value = order_mock
        limit_mock = MagicMock()
        limit_mock.eq.return_value = eq_mock
        select_mock = MagicMock()
        select_mock.limit.return_value = limit_mock
        table_mock = MagicMock()
        table_mock.select.return_value = select_mock
        mock_supabase_client.table.return_value = table_mock

        # Execute
        result = await repository.get_all_api_keys(limit=50, include_inactive=False)

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], ApiKey)
        assert result[0].id == sample_api_key.id
        select_mock.limit.assert_called_once_with(50)
        limit_mock.eq.assert_called_once_with("is_active", True)
        eq_mock.order.assert_called_once_with("created_at", desc=True)

    async def test_get_all_api_keys_include_inactive(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
        sample_api_key: ApiKey,
    ):
        """Test getting all API keys including inactive ones."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.data = [sample_api_key.model_dump(mode="json")]

        # Setup mock chain
        execute_mock = AsyncMock(return_value=mock_response)
        order_mock = MagicMock()
        order_mock.execute = execute_mock
        limit_mock = MagicMock()
        limit_mock.order.return_value = order_mock
        select_mock = MagicMock()
        select_mock.limit.return_value = limit_mock
        table_mock = MagicMock()
        table_mock.select.return_value = select_mock
        mock_supabase_client.table.return_value = table_mock

        # Execute
        result = await repository.get_all_api_keys(include_inactive=True)

        # Verify
        assert len(result) == 1
        limit_mock.order.assert_called_once_with("created_at", desc=True)
        # Should not call eq() for is_active filter

    async def test_update_api_key_success(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
        sample_api_key: ApiKey,
    ):
        """Test successful API key update."""
        # Setup mock response
        updated_data = sample_api_key.model_dump(mode="json")
        updated_data["name"] = "Updated Name"
        mock_response = MagicMock()
        mock_response.data = [updated_data]

        # Setup mock chain
        execute_mock = AsyncMock(return_value=mock_response)
        eq_mock = MagicMock()
        eq_mock.execute = execute_mock
        update_mock = MagicMock()
        update_mock.eq.return_value = eq_mock
        table_mock = MagicMock()
        table_mock.update.return_value = update_mock
        mock_supabase_client.table.return_value = table_mock

        # Execute
        update_data = ApiKeyUpdate(name="Updated Name")
        result = await repository.update_api_key(sample_api_key.id, update_data)

        # Verify
        assert isinstance(result, ApiKey)
        assert result.name == "Updated Name"
        table_mock.update.assert_called_once()
        update_mock.eq.assert_called_once_with("id", str(sample_api_key.id))

    async def test_update_api_key_no_fields(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
        sample_api_key: ApiKey,
    ):
        """Test API key update with no fields to update."""
        # Setup mock for get_api_key call
        mock_response = MagicMock()
        mock_response.data = [sample_api_key.model_dump(mode="json")]

        # Setup mock chain for select (get_api_key)
        execute_mock = AsyncMock(return_value=mock_response)
        eq_mock = MagicMock()
        eq_mock.execute = execute_mock
        select_mock = MagicMock()
        select_mock.eq.return_value = eq_mock
        table_mock = MagicMock()
        table_mock.select.return_value = select_mock
        mock_supabase_client.table.return_value = table_mock

        # Execute
        update_data = ApiKeyUpdate()  # No fields set
        result = await repository.update_api_key(sample_api_key.id, update_data)

        # Verify
        assert isinstance(result, ApiKey)
        assert result.id == sample_api_key.id
        # Should have called get_api_key, not update
        table_mock.select.assert_called_once_with("*")

    async def test_update_api_key_not_found(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
    ):
        """Test updating an API key that doesn't exist."""
        # Setup mock response with no data
        mock_response = MagicMock()
        mock_response.data = []

        # Setup mock chain
        execute_mock = AsyncMock(return_value=mock_response)
        eq_mock = MagicMock()
        eq_mock.execute = execute_mock
        update_mock = MagicMock()
        update_mock.eq.return_value = eq_mock
        table_mock = MagicMock()
        table_mock.update.return_value = update_mock
        mock_supabase_client.table.return_value = table_mock

        # Execute
        update_data = ApiKeyUpdate(name="Updated Name")
        result = await repository.update_api_key(uuid.uuid4(), update_data)

        # Verify
        assert result is None

    async def test_delete_api_key_success(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
        sample_api_key: ApiKey,
    ):
        """Test successful API key deletion (soft delete)."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.data = [{"id": str(sample_api_key.id)}]

        # Setup mock chain
        execute_mock = AsyncMock(return_value=mock_response)
        eq_mock = MagicMock()
        eq_mock.execute = execute_mock
        update_mock = MagicMock()
        update_mock.eq.return_value = eq_mock
        table_mock = MagicMock()
        table_mock.update.return_value = update_mock
        mock_supabase_client.table.return_value = table_mock

        # Execute
        result = await repository.delete_api_key(sample_api_key.id)

        # Verify
        assert result is True
        table_mock.update.assert_called_once_with({"is_active": False})
        update_mock.eq.assert_called_once_with("id", str(sample_api_key.id))

    async def test_delete_api_key_not_found(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
    ):
        """Test deleting an API key that doesn't exist."""
        # Setup mock response with no data
        mock_response = MagicMock()
        mock_response.data = []

        # Setup mock chain
        execute_mock = AsyncMock(return_value=mock_response)
        eq_mock = MagicMock()
        eq_mock.execute = execute_mock
        update_mock = MagicMock()
        update_mock.eq.return_value = eq_mock
        table_mock = MagicMock()
        table_mock.update.return_value = update_mock
        mock_supabase_client.table.return_value = table_mock

        # Execute
        result = await repository.delete_api_key(uuid.uuid4())

        # Verify
        assert result is False

    async def test_increment_usage_success(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
        sample_api_key: ApiKey,
    ):
        """Test successful usage increment."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.data = {"success": True}

        # Setup mock chain
        execute_mock = AsyncMock(return_value=mock_response)
        rpc_mock = MagicMock()
        rpc_mock.execute = execute_mock
        mock_supabase_client.rpc.return_value = rpc_mock

        # Execute
        result = await repository.increment_usage(sample_api_key.id)

        # Verify
        assert result is True
        mock_supabase_client.rpc.assert_called_once_with(
            "increment_api_key_usage", {"key_id": str(sample_api_key.id)}
        )

    async def test_increment_usage_failure(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
        sample_api_key: ApiKey,
    ):
        """Test usage increment failure."""
        # Setup mock to raise exception
        execute_mock = AsyncMock(side_effect=Exception("Database error"))
        rpc_mock = MagicMock()
        rpc_mock.execute = execute_mock
        mock_supabase_client.rpc.return_value = rpc_mock

        # Execute
        result = await repository.increment_usage(sample_api_key.id)

        # Verify
        assert result is False

    async def test_get_api_key_stats_with_data(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
    ):
        """Test getting API key statistics when data exists."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.data = [
            {"id": "key1", "is_active": True, "usage_count": 100},
            {"id": "key2", "is_active": True, "usage_count": 50},
            {"id": "key3", "is_active": False, "usage_count": 25},
        ]

        # Setup mock chain for initial stats query
        execute_mock = AsyncMock(return_value=mock_response)
        select_mock = MagicMock()
        select_mock.execute = execute_mock
        table_mock = MagicMock()
        table_mock.select.return_value = select_mock

        # Setup mock for most active key query
        most_active_response = MagicMock()
        most_active_response.data = [{"key_prefix": "sk_live_abcd"}]
        execute_mock2 = AsyncMock(return_value=most_active_response)
        eq_mock = MagicMock()
        eq_mock.execute = execute_mock2
        select_mock2 = MagicMock()
        select_mock2.eq.return_value = eq_mock

        # Configure side effects for different calls
        def table_side_effect(table_name):
            if table_name == "api_keys":
                # First call for stats
                mock_table = MagicMock()
                mock_table.select.return_value = select_mock
                return mock_table
            return table_mock

        mock_supabase_client.table.side_effect = [table_mock, table_mock]
        table_mock.select.side_effect = [select_mock, select_mock2]

        # Execute
        result = await repository.get_api_key_stats()

        # Verify
        assert isinstance(result, ApiKeyStats)
        assert result.total_keys == 3
        assert result.active_keys == 2
        assert result.inactive_keys == 1
        assert result.total_requests == 175  # 100 + 50 + 25

    async def test_get_api_key_stats_no_data(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
    ):
        """Test getting API key statistics when no data exists."""
        # Setup mock response with no data
        mock_response = MagicMock()
        mock_response.data = []

        # Setup mock chain
        execute_mock = AsyncMock(return_value=mock_response)
        select_mock = MagicMock()
        select_mock.execute = execute_mock
        table_mock = MagicMock()
        table_mock.select.return_value = select_mock
        mock_supabase_client.table.return_value = table_mock

        # Execute
        result = await repository.get_api_key_stats()

        # Verify
        assert isinstance(result, ApiKeyStats)
        assert result.total_keys == 0
        assert result.active_keys == 0
        assert result.inactive_keys == 0
        assert result.total_requests == 0

    async def test_find_keys_by_name(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
        sample_api_key: ApiKey,
    ):
        """Test finding API keys by name pattern."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.data = [sample_api_key.model_dump(mode="json")]

        # Setup mock chain
        execute_mock = AsyncMock(return_value=mock_response)
        order_mock = MagicMock()
        order_mock.execute = execute_mock
        ilike_mock = MagicMock()
        ilike_mock.order.return_value = order_mock
        select_mock = MagicMock()
        select_mock.ilike.return_value = ilike_mock
        table_mock = MagicMock()
        table_mock.select.return_value = select_mock
        mock_supabase_client.table.return_value = table_mock

        # Execute
        result = await repository.find_keys_by_name("test")

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], ApiKey)
        select_mock.ilike.assert_called_once_with("name", "%test%")
        ilike_mock.order.assert_called_once_with("created_at", desc=True)

    async def test_count_active_keys(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
    ):
        """Test counting active API keys."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.count = 5

        # Setup mock chain
        execute_mock = AsyncMock(return_value=mock_response)
        eq_mock = MagicMock()
        eq_mock.execute = execute_mock
        select_mock = MagicMock()
        select_mock.eq.return_value = eq_mock
        table_mock = MagicMock()
        table_mock.select.return_value = select_mock
        mock_supabase_client.table.return_value = table_mock

        # Execute
        result = await repository.count_active_keys()

        # Verify
        assert result == 5
        table_mock.select.assert_called_once_with("id", count="exact")
        select_mock.eq.assert_called_once_with("is_active", True)

    async def test_count_active_keys_no_count(
        self,
        repository: ApiKeyRepository,
        mock_supabase_client: MagicMock,
    ):
        """Test counting active API keys when count is None."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.count = None

        # Setup mock chain
        execute_mock = AsyncMock(return_value=mock_response)
        eq_mock = MagicMock()
        eq_mock.execute = execute_mock
        select_mock = MagicMock()
        select_mock.eq.return_value = eq_mock
        table_mock = MagicMock()
        table_mock.select.return_value = select_mock
        mock_supabase_client.table.return_value = table_mock

        # Execute
        result = await repository.count_active_keys()

        # Verify
        assert result == 0
