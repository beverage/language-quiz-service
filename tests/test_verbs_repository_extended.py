"""Extended tests for the VerbRepository."""

import pytest
from unittest.mock import MagicMock, AsyncMock, call
from uuid import uuid4
from datetime import datetime, timezone

from src.repositories.verb_repository import VerbRepository
from src.schemas.verbs import (
    Verb,
    Conjugation,
    Tense,
    AuxiliaryType as Auxiliary,
    VerbWithConjugations,
    VerbCreate,
    ConjugationCreate,
)


@pytest.fixture
def mock_supabase_client():
    """A local, specific mock for the Supabase client for extended tests."""
    mock_client = MagicMock()

    # This mock is designed to be flexible for chaining.
    # Each method call returns the mock itself, allowing for chained calls.
    # The final `execute` is an AsyncMock to simulate the async database call.
    mock_chain = MagicMock()
    mock_chain.select.return_value = mock_chain
    mock_chain.insert.return_value = mock_chain
    mock_chain.update.return_value = mock_chain
    mock_chain.delete.return_value = mock_chain
    mock_chain.eq.return_value = mock_chain
    mock_chain.in_.return_value = mock_chain
    mock_chain.limit.return_value = mock_chain
    mock_chain.or_.return_value = mock_chain
    mock_chain.ilike.return_value = mock_chain
    mock_chain.execute = AsyncMock()

    mock_client.table.return_value = mock_chain
    mock_client.rpc.return_value.execute = AsyncMock()
    return mock_client


@pytest.fixture
def verb_repository(mock_supabase_client):
    """Fixture for the VerbRepository with a mocked Supabase client."""
    return VerbRepository(client=mock_supabase_client)


@pytest.fixture
def sample_verb_id():
    return uuid4()


@pytest.fixture
def sample_db_verb(sample_verb_id):
    """A complete Verb object as it would exist in the database."""
    return Verb(
        id=sample_verb_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        infinitive="aller",
        target_language_code="fra",
        reflexive=False,
        auxiliary=Auxiliary.ETRE,
        translation="to go",
        present_participle="allant",
        past_participle="allé",
        last_used_at=None,
    )


@pytest.fixture
def sample_db_conjugation(sample_db_verb):
    """A sample conjugation object."""
    return Conjugation(
        id=uuid4(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        infinitive=sample_db_verb.infinitive,
        auxiliary=sample_db_verb.auxiliary,
        reflexive=sample_db_verb.reflexive,
        tense=Tense.PRESENT,
        first_person_singular="vais",
        second_person_singular="vas",
        third_person_singular="va",
        first_person_plural="allons",
        second_person_formal="allez",
        third_person_plural="vont",
    )


# --- Verb Tests ---


@pytest.mark.asyncio
async def test_get_verb_by_infinitive_with_all_params(
    verb_repository, mock_supabase_client, sample_db_verb
):
    # Arrange
    execute_mock = mock_supabase_client.table.return_value.execute
    execute_mock.return_value.data = [sample_db_verb.model_dump()]

    # Act
    result = await verb_repository.get_verb_by_infinitive(
        infinitive="aller",
        auxiliary="être",
        reflexive=False,
        target_language_code="fra",
    )

    # Assert
    assert result is not None
    assert result.infinitive == "aller"
    eq_mock = mock_supabase_client.table.return_value.eq
    eq_mock.assert_has_calls(
        [
            call("infinitive", "aller"),
            call("auxiliary", "être"),
            call("reflexive", False),
            call("target_language_code", "fra"),
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_get_verbs_by_infinitive(
    verb_repository, mock_supabase_client, sample_db_verb
):
    # Arrange
    execute_mock = mock_supabase_client.table.return_value.execute
    execute_mock.return_value.data = [
        sample_db_verb.model_dump(),
        sample_db_verb.model_dump() | {"reflexive": True},
    ]

    # Act
    results = await verb_repository.get_verbs_by_infinitive(infinitive="aller")

    # Assert
    assert len(results) == 2
    mock_supabase_client.table.return_value.eq.assert_called_once_with(
        "infinitive", "aller"
    )


@pytest.mark.asyncio
async def test_get_all_verbs_with_filter(
    verb_repository, mock_supabase_client, sample_db_verb
):
    # Arrange
    execute_mock = mock_supabase_client.table.return_value.execute
    execute_mock.return_value.data = [sample_db_verb.model_dump()]

    # Act
    await verb_repository.get_all_verbs(limit=50, target_language_code="fra")

    # Assert
    mock_supabase_client.table.return_value.limit.assert_called_with(50)
    mock_supabase_client.table.return_value.eq.assert_called_with(
        "target_language_code", "fra"
    )


@pytest.mark.asyncio
async def test_get_random_verb(verb_repository, mock_supabase_client, sample_db_verb):
    # Arrange
    # Mock the RPC call
    rpc_execute_mock = mock_supabase_client.rpc.return_value.execute
    rpc_execute_mock.return_value.data = [sample_db_verb.model_dump()]

    # Act
    result = await verb_repository.get_random_verb(target_language_code="fra")

    # Assert
    assert result is not None
    assert result.infinitive == "aller"
    mock_supabase_client.rpc.assert_called_with(
        "get_random_verb_simple", {"p_target_language": "fra"}
    )


# --- Conjugation Tests ---


@pytest.mark.asyncio
async def test_get_conjugations(
    verb_repository, mock_supabase_client, sample_db_conjugation
):
    # Arrange
    execute_mock = mock_supabase_client.table.return_value.execute
    execute_mock.return_value.data = [sample_db_conjugation.model_dump()]

    # Act
    results = await verb_repository.get_conjugations(
        infinitive="aller", auxiliary="être", reflexive=False
    )

    # Assert
    assert len(results) == 1
    assert results[0].tense == Tense.PRESENT
    eq_mock = mock_supabase_client.table.return_value.eq
    eq_mock.assert_has_calls(
        [
            call("infinitive", "aller"),
            call("auxiliary", "être"),
            call("reflexive", False),
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_get_verb_with_conjugations(
    verb_repository, mock_supabase_client, sample_db_verb, sample_db_conjugation
):
    # Arrange
    # The method under test now makes two calls:
    # 1. get_verb_by_infinitive
    # 2. get_conjugations
    # We need to mock the `execute` return value for both.

    # Mock response for the first call (get_verb_by_infinitive)
    mock_verb_response = MagicMock()
    mock_verb_response.data = [sample_db_verb.model_dump()]

    # Mock response for the second call (get_conjugations)
    mock_conjugation_response = MagicMock()
    mock_conjugation_response.data = [sample_db_conjugation.model_dump()]

    execute_mock = mock_supabase_client.table.return_value.execute
    execute_mock.side_effect = [
        mock_verb_response,
        mock_conjugation_response,
    ]

    # Act
    result = await verb_repository.get_verb_with_conjugations(
        infinitive="aller",
        auxiliary=sample_db_verb.auxiliary.value,
        reflexive=False,
        target_language_code="fra",
    )

    # Assert
    assert result is not None
    assert isinstance(result, VerbWithConjugations)
    assert result.infinitive == "aller"
    assert len(result.conjugations) == 1
    assert result.conjugations[0].tense == Tense.PRESENT
    assert execute_mock.call_count == 2


@pytest.mark.asyncio
async def test_search_verbs(verb_repository, mock_supabase_client, sample_db_verb):
    # Arrange
    rpc_mock = mock_supabase_client.rpc.return_value.execute
    rpc_mock.return_value.data = [sample_db_verb.model_dump()]
    mock_supabase_client.table.return_value.execute.return_value.data = [
        sample_db_verb.model_dump()
    ]

    # Act
    results = await verb_repository.search_verbs(query="aller", limit=5)

    # Assert
    assert len(results) > 0
    assert results[0].infinitive == "aller"
    mock_supabase_client.table.return_value.or_.assert_called_once()


# --- Upsert Tests ---


@pytest.fixture
def sample_verb_create(sample_db_verb):
    """A VerbCreate object for tests."""
    return VerbCreate.model_validate(sample_db_verb.model_dump())


@pytest.mark.asyncio
async def test_upsert_verb_creates_new_verb(
    verb_repository, mock_supabase_client, sample_verb_create, sample_db_verb
):
    # Arrange
    # First call to get_verb_by_infinitive returns nothing
    mock_get_response = MagicMock()
    mock_get_response.data = []
    # Second call to insert returns the new verb
    mock_insert_response = MagicMock()
    mock_insert_response.data = [sample_db_verb.model_dump()]

    execute_mock = mock_supabase_client.table.return_value.execute
    execute_mock.side_effect = [mock_get_response, mock_insert_response]

    # Act
    result = await verb_repository.upsert_verb(sample_verb_create)

    # Assert
    assert result.id == sample_db_verb.id
    assert execute_mock.call_count == 2
    mock_supabase_client.table.return_value.insert.assert_called_once_with(
        sample_verb_create.model_dump()
    )


@pytest.mark.asyncio
async def test_upsert_verb_updates_existing_verb(
    verb_repository, mock_supabase_client, sample_verb_create, sample_db_verb
):
    # Arrange
    # First call to get_verb_by_infinitive returns the existing verb
    mock_get_response = MagicMock()
    mock_get_response.data = [sample_db_verb.model_dump()]
    # Second call to update returns the updated verb
    mock_update_response = MagicMock()
    mock_update_response.data = [sample_db_verb.model_dump()]

    execute_mock = mock_supabase_client.table.return_value.execute
    execute_mock.side_effect = [mock_get_response, mock_update_response]

    # Act
    result = await verb_repository.upsert_verb(sample_verb_create)

    # Assert
    assert result.id == sample_db_verb.id
    assert execute_mock.call_count == 2
    mock_supabase_client.table.return_value.update.assert_called_once()


@pytest.fixture
def sample_conjugation_create(sample_db_conjugation):
    """A ConjugationCreate object for tests."""
    return ConjugationCreate.model_validate(sample_db_conjugation.model_dump())


@pytest.mark.asyncio
async def test_upsert_conjugation_creates_new(
    verb_repository,
    mock_supabase_client,
    sample_conjugation_create,
    sample_db_conjugation,
):
    # Arrange
    mock_get_response = MagicMock()
    mock_get_response.data = []
    mock_insert_response = MagicMock()
    mock_insert_response.data = [sample_db_conjugation.model_dump()]

    execute_mock = mock_supabase_client.table.return_value.execute
    execute_mock.side_effect = [mock_get_response, mock_insert_response]

    # Act
    await verb_repository.upsert_conjugation(sample_conjugation_create)

    # Assert
    assert execute_mock.call_count == 2
    mock_supabase_client.table.return_value.insert.assert_called_once()


@pytest.mark.asyncio
async def test_upsert_conjugation_updates_existing(
    verb_repository,
    mock_supabase_client,
    sample_conjugation_create,
    sample_db_conjugation,
):
    # Arrange
    mock_get_response = MagicMock()
    mock_get_response.data = [sample_db_conjugation.model_dump()]
    mock_update_response = MagicMock()
    mock_update_response.data = [sample_db_conjugation.model_dump()]

    execute_mock = mock_supabase_client.table.return_value.execute
    execute_mock.side_effect = [mock_get_response, mock_update_response]

    # Act
    await verb_repository.upsert_conjugation(sample_conjugation_create)

    # Assert
    assert execute_mock.call_count == 2
    mock_supabase_client.table.return_value.update.assert_called_once()
