"""Unit tests for the verb repository."""

import uuid
from unittest.mock import MagicMock, AsyncMock

import pytest

from src.repositories.verb_repository import VerbRepository
from src.schemas.verbs import VerbCreate, VerbUpdate
from src.schemas.verbs import Verb


@pytest.fixture
def mock_supabase_client() -> MagicMock:
    """Provides a mock Supabase client for testing."""
    mock_client = MagicMock()

    # Mock the chain of calls for select
    select_mock = MagicMock()
    select_mock.eq.return_value = select_mock
    select_mock.limit.return_value = select_mock
    select_mock.execute = AsyncMock()

    # Mock the chain of calls for update
    update_mock = MagicMock()
    update_mock.eq.return_value = update_mock
    update_mock.execute = AsyncMock()

    # Mock the chain of calls for insert
    insert_mock = MagicMock()
    insert_mock.execute = AsyncMock()

    # Mock the chain of calls for delete
    delete_mock = MagicMock()
    delete_mock.eq.return_value = delete_mock
    delete_mock.execute = AsyncMock()

    # Mock the rpc call
    rpc_mock = MagicMock()
    rpc_mock.execute = AsyncMock()

    # Mock the table method to return a mock that has the chained methods
    table_mock = MagicMock()
    table_mock.select.return_value = select_mock
    table_mock.update.return_value = update_mock
    table_mock.insert.return_value = insert_mock
    table_mock.delete.return_value = delete_mock

    mock_client.table.return_value = table_mock
    mock_client.rpc.return_value = rpc_mock
    return mock_client


@pytest.fixture
def repository(mock_supabase_client: MagicMock) -> VerbRepository:
    """Provides a VerbRepository instance with a mocked Supabase client."""
    return VerbRepository(client=mock_supabase_client)


@pytest.mark.unit
@pytest.mark.asyncio
class TestVerbRepository:
    """Test cases for the VerbRepository."""

    async def test_create_verb_success(
        self,
        repository: VerbRepository,
        mock_supabase_client: MagicMock,
        sample_db_verb: Verb,
    ):
        """Tests successful creation of a verb."""
        mock_response = MagicMock()
        mock_response.data = [sample_db_verb.model_dump()]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response

        verb_create = VerbCreate(**sample_db_verb.model_dump())
        created_verb = await repository.create_verb(verb_create)

        assert created_verb is not None
        assert created_verb.infinitive == sample_db_verb.infinitive
        mock_supabase_client.table.return_value.insert.assert_called_once_with(
            verb_create.model_dump()
        )

    async def test_create_verb_failure(
        self,
        repository: VerbRepository,
        mock_supabase_client: MagicMock,
        sample_verb_data: dict,
    ):
        """Tests failure during verb creation."""
        error_message = "DB Error"
        mock_supabase_client.table.return_value.insert.return_value.execute.side_effect = Exception(
            error_message
        )
        verb_create = VerbCreate(**sample_verb_data)

        with pytest.raises(Exception) as excinfo:
            await repository.create_verb(verb_create)
        assert error_message in str(excinfo.value)

    async def test_get_verb_found(
        self,
        repository: VerbRepository,
        mock_supabase_client: MagicMock,
        sample_db_verb: Verb,
    ):
        """Tests retrieving a verb that exists."""
        mock_response = MagicMock()
        mock_response.data = [sample_db_verb.model_dump()]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        verb = await repository.get_verb(sample_db_verb.id)

        assert verb is not None
        assert verb.id == sample_db_verb.id
        mock_supabase_client.table.return_value.select.return_value.eq.assert_called_once_with(
            "id", str(sample_db_verb.id)
        )

    async def test_get_verb_not_found(
        self, repository: VerbRepository, mock_supabase_client: MagicMock
    ):
        """Tests retrieving a verb that does not exist."""
        verb_id = uuid.uuid4()
        mock_response = MagicMock()
        mock_response.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        verb = await repository.get_verb(verb_id)

        assert verb is None

    async def test_update_verb_success(
        self,
        repository: VerbRepository,
        mock_supabase_client: MagicMock,
        sample_db_verb: Verb,
    ):
        """Tests successfully updating a verb."""
        update_data = VerbUpdate(infinitive="new infinitive", reflexive=True)

        updated_verb_data = sample_db_verb.model_dump()
        updated_verb_data["infinitive"] = "new infinitive"
        updated_verb_data["reflexive"] = True

        mock_response = MagicMock()
        mock_response.data = [updated_verb_data]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        updated_verb = await repository.update_verb(sample_db_verb.id, update_data)

        assert updated_verb is not None
        assert updated_verb.infinitive == "new infinitive"
        assert updated_verb.reflexive is True
        mock_supabase_client.table.return_value.update.assert_called_once_with(
            update_data.model_dump(exclude_unset=True)
        )

    async def test_delete_verb_success(
        self, repository: VerbRepository, mock_supabase_client: MagicMock
    ):
        """Tests successfully deleting a verb."""
        verb_id = uuid.uuid4()
        mock_response = MagicMock()
        mock_response.data = [1]  # Simulate successful deletion response
        mock_supabase_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_response

        result = await repository.delete_verb(verb_id)

        assert result is True
        mock_supabase_client.table.return_value.delete.return_value.eq.assert_called_once_with(
            "id", str(verb_id)
        )

    async def test_delete_verb_not_found(
        self, repository: VerbRepository, mock_supabase_client: MagicMock
    ):
        """Tests deleting a verb that does not exist."""
        verb_id = uuid.uuid4()
        mock_response = MagicMock()
        mock_response.data = []  # Simulate not found response
        mock_supabase_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_response

        result = await repository.delete_verb(verb_id)

        assert result is False
