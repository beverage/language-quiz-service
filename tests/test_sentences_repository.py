"""Unit tests for the sentence repository."""

import uuid
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from src.repositories.sentence_repository import SentenceRepository
from src.schemas.sentences import Sentence, SentenceCreate, SentenceUpdate


@pytest.fixture
def mock_supabase_client() -> MagicMock:
    """Provides a mock Supabase client for testing."""
    mock_client = MagicMock()

    # Mock the chain of calls for select
    select_mock = MagicMock()
    select_mock.eq.return_value = select_mock
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

    # Mock the table method to return a mock that has the chained methods
    table_mock = MagicMock()
    table_mock.select.return_value = select_mock
    table_mock.update.return_value = update_mock
    table_mock.insert.return_value = insert_mock
    table_mock.delete.return_value = delete_mock

    mock_client.table.return_value = table_mock
    return mock_client


@pytest.fixture
def repository(mock_supabase_client: MagicMock) -> SentenceRepository:
    """Provides a SentenceRepository instance with a mocked Supabase client."""
    with patch(
        "src.repositories.sentence_repository.get_supabase_client",
        return_value=mock_supabase_client,
    ) as mock_get_client:
        repo = SentenceRepository()
        mock_get_client.assert_called_once()
    return repo


@pytest.mark.unit
@pytest.mark.asyncio
class TestSentenceRepository:
    """Test cases for the SentenceRepository."""

    @pytest.fixture
    def repository(self, mock_supabase_client: MagicMock) -> SentenceRepository:
        """Fixture to create a SentenceRepository with a mock client."""
        return SentenceRepository(client=mock_supabase_client)

    async def test_create_sentence_success(
        self,
        repository: SentenceRepository,
        mock_supabase_client: MagicMock,
        sample_db_sentence: Sentence,
    ):
        """Tests successful creation of a sentence."""
        mock_response = MagicMock()
        mock_response.data = [sample_db_sentence.model_dump(mode="json")]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response

        sentence_create = SentenceCreate(**sample_db_sentence.model_dump())
        created_sentence = await repository.create_sentence(sentence_create)

        assert created_sentence is not None
        assert created_sentence.content == sample_db_sentence.content
        repository.client.table.return_value.insert.assert_called_once()

    async def test_get_sentence_found(
        self,
        repository: SentenceRepository,
        mock_supabase_client: MagicMock,
        sample_db_sentence: Sentence,
    ):
        """Tests retrieving a sentence that exists."""
        mock_response = MagicMock()
        mock_response.data = [sample_db_sentence.model_dump(mode="json")]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        sentence = await repository.get_sentence(sample_db_sentence.id)

        assert sentence is not None
        assert sentence.id == sample_db_sentence.id
        repository.client.table.return_value.select.return_value.eq.assert_called_once_with(
            "id", str(sample_db_sentence.id)
        )

    async def test_get_sentence_not_found(
        self, repository: SentenceRepository, mock_supabase_client: MagicMock
    ):
        """Tests retrieving a sentence that does not exist."""
        sentence_id = uuid.uuid4()
        mock_response = MagicMock()
        mock_response.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        sentence = await repository.get_sentence(sentence_id)

        assert sentence is None

    async def test_update_sentence_success(
        self,
        repository: SentenceRepository,
        mock_supabase_client: MagicMock,
        sample_db_sentence: Sentence,
    ):
        """Tests successfully updating a sentence."""
        update_data = SentenceUpdate(is_correct=False)
        updated_sentence_data = sample_db_sentence.model_dump(mode="json")
        updated_sentence_data["is_correct"] = False

        mock_response = MagicMock()
        mock_response.data = [updated_sentence_data]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        updated_sentence = await repository.update_sentence(
            sample_db_sentence.id, update_data
        )

        assert updated_sentence is not None
        assert updated_sentence.is_correct is False
        repository.client.table.return_value.update.assert_called_once_with(
            update_data.model_dump(exclude_unset=True)
        )

    async def test_delete_sentence_success(
        self, repository: SentenceRepository, mock_supabase_client: MagicMock
    ):
        """Tests successfully deleting a sentence."""
        sentence_id = uuid.uuid4()
        mock_response = MagicMock()
        mock_response.data = [1]
        mock_supabase_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_response

        result = await repository.delete_sentence(sentence_id)

        assert result is True
        repository.client.table.return_value.delete.return_value.eq.assert_called_once_with(
            "id", str(sentence_id)
        )
