"""Extended tests for the SentenceRepository."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

from src.repositories.sentence_repository import SentenceRepository
from src.schemas.sentences import (
    Sentence,
    SentenceCreate,
    SentenceUpdate,
    Pronoun,
    Tense,
)


@pytest.fixture
def mock_supabase_client():
    """A flexible mock for the Supabase client for extended tests."""
    mock_client = MagicMock()
    mock_chain = MagicMock()

    # Configure chainable methods
    for method in [
        "select",
        "insert",
        "update",
        "delete",
        "eq",
        "in_",
        "limit",
        "or_",
        "ilike",
    ]:
        setattr(mock_chain, method, MagicMock(return_value=mock_chain))

    mock_chain.execute = AsyncMock()
    mock_client.table.return_value = mock_chain
    mock_client.rpc.return_value.execute = AsyncMock()
    return mock_client


@pytest.fixture
def repository(mock_supabase_client: MagicMock) -> SentenceRepository:
    """Fixture to create a SentenceRepository with a mock client."""
    return SentenceRepository(client=mock_supabase_client)


@pytest.mark.asyncio
async def test_create_repository_with_new_client():
    """Tests that the repository creates a new client if one is not provided."""
    with patch(
        "src.repositories.sentence_repository.get_supabase_client",
        new_callable=AsyncMock,
    ) as mock_get_client:
        repo = await SentenceRepository.create()
        mock_get_client.assert_awaited_once()
        assert repo.client == mock_get_client.return_value


@pytest.mark.asyncio
async def test_create_sentence_failure(
    repository: SentenceRepository, sample_db_sentence: Sentence
):
    """Tests the failure path of creating a sentence."""
    repository.client.table.return_value.insert.return_value.execute.return_value.data = None
    sentence_create = SentenceCreate(**sample_db_sentence.model_dump())

    with pytest.raises(Exception, match="Failed to create sentence"):
        await repository.create_sentence(sentence_create)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "filter_key, filter_value, expected_call",
    [
        ("verb_id", uuid4(), lambda v: ("verb_id", str(v))),
        ("is_correct", True, ("is_correct", True)),
        ("is_correct", False, ("is_correct", False)),
        ("tense", Tense.PRESENT, ("tense", "present")),
        ("pronoun", Pronoun.FIRST_PERSON, ("pronoun", "first_person")),
        ("target_language_code", "eng", ("target_language_code", "eng")),
    ],
)
async def test_get_sentences_with_filters(
    repository: SentenceRepository, filter_key, filter_value, expected_call
):
    """Tests get_sentences with various filters."""
    repository.client.table.return_value.select.return_value.limit.return_value.execute.return_value.data = []

    kwargs = {filter_key: filter_value}
    await repository.get_sentences(**kwargs)

    # Resolve the expected call if it's a lambda
    if callable(expected_call):
        expected_call = expected_call(filter_value)

    repository.client.table.return_value.select.return_value.eq.assert_called_once_with(
        *expected_call
    )
    repository.client.table.return_value.select.return_value.limit.assert_called_once_with(
        50
    )


@pytest.mark.asyncio
async def test_get_sentences_by_verb(repository: SentenceRepository):
    """Tests getting sentences by verb ID."""
    verb_id = uuid4()
    with patch.object(repository, "get_sentences", new_callable=AsyncMock) as mock_get:
        await repository.get_sentences_by_verb(verb_id, limit=10)
        mock_get.assert_awaited_once_with(verb_id=verb_id, limit=10)


@pytest.mark.asyncio
@pytest.mark.parametrize("is_correct_filter", [True, False, None])
async def test_get_random_sentence(
    repository: SentenceRepository,
    sample_db_sentence: Sentence,
    is_correct_filter: bool,
):
    """Tests getting a random sentence with and without filters."""
    repository.client.table.return_value.select.return_value.limit.return_value.execute.return_value.data = [
        sample_db_sentence.model_dump(mode="json")
    ]

    result = await repository.get_random_sentence(is_correct=is_correct_filter)

    assert result is not None
    assert result.id == sample_db_sentence.id

    if is_correct_filter is not None:
        repository.client.table.return_value.select.return_value.eq.assert_called_with(
            "is_correct", is_correct_filter
        )


@pytest.mark.asyncio
async def test_get_random_sentence_not_found(repository: SentenceRepository):
    """Tests get_random_sentence when no sentences are found."""
    repository.client.table.return_value.select.return_value.limit.return_value.execute.return_value.data = []
    result = await repository.get_random_sentence()
    assert result is None


@pytest.mark.asyncio
async def test_update_sentence_not_found(repository: SentenceRepository):
    """Tests update_sentence when the sentence is not found."""
    repository.client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []
    result = await repository.update_sentence(uuid4(), SentenceUpdate(is_correct=True))
    assert result is None


@pytest.mark.asyncio
async def test_delete_sentence_not_found(repository: SentenceRepository):
    """Tests delete_sentence when the sentence is not found."""
    repository.client.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = []
    result = await repository.delete_sentence(uuid4())
    assert result is False


@pytest.mark.asyncio
async def test_get_all_sentences(
    repository: SentenceRepository, sample_db_sentence: Sentence
):
    """Tests getting all sentences."""
    repository.client.table.return_value.select.return_value.limit.return_value.execute.return_value.data = [
        sample_db_sentence.model_dump(mode="json")
    ]
    result = await repository.get_all_sentences(limit=10)
    assert len(result) == 1
    assert result[0].id == sample_db_sentence.id
    repository.client.table.return_value.select.return_value.limit.assert_called_once_with(
        10
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "verb_id_filter, is_correct_filter",
    [(uuid4(), True), (None, False), (uuid4(), None), (None, None)],
)
async def test_count_sentences(
    repository: SentenceRepository, verb_id_filter, is_correct_filter
):
    """Tests counting sentences with various filters."""
    repository.client.table.return_value.select.return_value.execute.return_value.count = 5

    kwargs = {}
    if verb_id_filter:
        kwargs["verb_id"] = verb_id_filter
    if is_correct_filter is not None:
        kwargs["is_correct"] = is_correct_filter

    count = await repository.count_sentences(**kwargs)
    assert count == 5

    eq_calls = repository.client.table.return_value.select.return_value.eq.call_count
    expected_calls = 0
    if verb_id_filter:
        expected_calls += 1
    if is_correct_filter is not None:
        expected_calls += 1
    assert eq_calls == expected_calls
