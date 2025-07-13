"""Unit tests for the verb repository."""

from unittest.mock import MagicMock, AsyncMock

import pytest

from src.repositories.verb_repository import VerbRepository
from src.schemas.verbs import VerbCreate, VerbUpdate


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
@pytest.mark.parametrize(
    "method,setup_fn,call_args,expected_result,raises",
    [
        (
            "create_verb",
            lambda repo,
            client,
            verb: client.table.return_value.insert.return_value.execute.return_value.__setattr__(
                "data", [verb.model_dump()]
            ),
            lambda verb: (VerbCreate(**verb.model_dump()),),
            lambda verb: verb.infinitive,
            None,
        ),
        (
            "get_verb",
            lambda repo,
            client,
            verb: client.table.return_value.select.return_value.eq.return_value.execute.return_value.__setattr__(
                "data", [verb.model_dump()]
            ),
            lambda verb: (verb.id,),
            lambda verb: verb.id,
            None,
        ),
        (
            "update_verb",
            lambda repo,
            client,
            verb: client.table.return_value.update.return_value.eq.return_value.execute.return_value.__setattr__(
                "data",
                [
                    verb.model_copy(
                        update={"infinitive": "new infinitive", "reflexive": True}
                    ).model_dump()
                ],
            ),
            lambda verb: (
                verb.id,
                VerbUpdate(infinitive="new infinitive", reflexive=True),
            ),
            lambda verb: "new infinitive",
            None,
        ),
        (
            "delete_verb",
            lambda repo,
            client,
            verb: client.table.return_value.delete.return_value.eq.return_value.execute.return_value.__setattr__(
                "data", [1]
            ),
            lambda verb: (verb.id,),
            lambda verb: True,
            None,
        ),
    ],
)
async def test_verb_repository_crud(
    repository,
    mock_supabase_client,
    sample_db_verb,
    method,
    setup_fn,
    call_args,
    expected_result,
    raises,
):
    setup_fn(repository, mock_supabase_client, sample_db_verb)
    args = call_args(sample_db_verb)
    if raises:
        with pytest.raises(raises):
            await getattr(repository, method)(*args)
    else:
        result = await getattr(repository, method)(*args)
        if method == "create_verb":
            assert result.infinitive == expected_result(sample_db_verb)
        elif method == "get_verb":
            assert result.id == expected_result(sample_db_verb)
        elif method == "update_verb":
            assert result.infinitive == expected_result(sample_db_verb)
        elif method == "delete_verb":
            assert result is expected_result(sample_db_verb)


@pytest.fixture
def chainable_mock_supabase_client():
    mock_client = MagicMock()
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
def extended_repository(chainable_mock_supabase_client):
    return VerbRepository(client=chainable_mock_supabase_client)


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,setup_fn,call_args,expected_result,raises",
    [
        (
            "get_verb_by_infinitive",
            lambda repo, client, verb: client.table.return_value.execute.__setattr__(
                "return_value", MagicMock(data=[verb.model_dump()])
            ),
            lambda verb: ("aller", "être", False, "fra"),
            lambda verb: verb.infinitive,
            None,
        ),
        (
            "get_verbs_by_infinitive",
            lambda repo, client, verb: client.table.return_value.execute.__setattr__(
                "return_value",
                MagicMock(
                    data=[verb.model_dump(), verb.model_dump() | {"reflexive": True}]
                ),
            ),
            lambda verb: ("aller",),
            lambda verb: 2,
            None,
        ),
        (
            "get_all_verbs",
            lambda repo, client, verb: client.table.return_value.execute.__setattr__(
                "return_value", MagicMock(data=[verb.model_dump()])
            ),
            lambda verb: (50, "fra"),
            lambda verb: 1,
            None,
        ),
        (
            "get_random_verb",
            lambda repo, client, verb: client.rpc.return_value.execute.__setattr__(
                "return_value", MagicMock(data=[verb.model_dump()])
            ),
            lambda verb: ("fra",),
            lambda verb: verb.infinitive,
            None,
        ),
    ],
)
async def test_verb_repository_retrieval_variants(
    extended_repository,
    chainable_mock_supabase_client,
    sample_db_verb,
    method,
    setup_fn,
    call_args,
    expected_result,
    raises,
):
    setup_fn(extended_repository, chainable_mock_supabase_client, sample_db_verb)
    args = call_args(sample_db_verb)
    if raises:
        with pytest.raises(raises):
            await getattr(extended_repository, method)(*args)
    else:
        result = await getattr(extended_repository, method)(*args)
        if method == "get_verbs_by_infinitive":
            assert len(result) == expected_result(sample_db_verb)
        elif method == "get_all_verbs":
            assert len(result) == expected_result(sample_db_verb)
        else:
            assert result.infinitive == expected_result(sample_db_verb)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_conjugation_by_verb_and_tense(
    repository, mock_supabase_client, sample_db_conjugation
):
    mock_response = MagicMock()
    mock_response.data = [sample_db_conjugation.model_dump()]
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
    result = await repository.get_conjugation_by_verb_and_tense(
        sample_db_conjugation.infinitive,
        sample_db_conjugation.auxiliary.value,
        sample_db_conjugation.reflexive,
        sample_db_conjugation.tense,
    )
    assert result == sample_db_conjugation


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_conjugation(repository, mock_supabase_client, sample_db_conjugation):
    mock_response = MagicMock()
    mock_response.data = [sample_db_conjugation.model_dump()]
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
    result = await repository.get_conjugation(
        sample_db_conjugation.infinitive,
        sample_db_conjugation.auxiliary.value,
        sample_db_conjugation.reflexive,
        sample_db_conjugation.tense,
    )
    assert result == sample_db_conjugation


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upsert_verb_create(
    repository, mock_supabase_client, sample_verb_create, sample_db_verb
):
    # Simulate no existing verb
    repository.get_verb_by_infinitive = AsyncMock(return_value=None)
    repository.create_verb = AsyncMock(return_value=sample_db_verb)
    result = await repository.upsert_verb(sample_verb_create)
    assert result == sample_db_verb
    repository.create_verb.assert_awaited_once_with(sample_verb_create)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upsert_verb_update(
    repository, mock_supabase_client, sample_verb_create, sample_db_verb
):
    # Simulate existing verb
    repository.get_verb_by_infinitive = AsyncMock(return_value=sample_db_verb)
    repository.update_verb = AsyncMock(return_value=sample_db_verb)
    result = await repository.upsert_verb(sample_verb_create)
    assert result == sample_db_verb
    repository.update_verb.assert_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_conjugation(
    repository, mock_supabase_client, sample_conjugation_create, sample_db_conjugation
):
    mock_response = MagicMock()
    mock_response.data = [sample_db_conjugation.model_dump()]
    mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
        mock_response
    )
    result = await repository.create_conjugation(sample_conjugation_create)
    assert result == sample_db_conjugation


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_conjugation_by_verb_and_tense(
    repository, mock_supabase_client, sample_conjugation_create, sample_db_conjugation
):
    from src.schemas.verbs import ConjugationUpdate

    update_data = ConjugationUpdate(first_person_singular="nouvelle forme")
    mock_response = MagicMock()
    mock_response.data = [sample_db_conjugation.model_dump()]
    mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response
    result = await repository.update_conjugation_by_verb_and_tense(
        sample_db_conjugation.infinitive,
        sample_db_conjugation.auxiliary.value,
        sample_db_conjugation.reflexive,
        sample_db_conjugation.tense,
        update_data,
    )
    assert result == sample_db_conjugation


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_conjugations_by_verb(
    repository, mock_supabase_client, sample_db_conjugation
):
    mock_response = MagicMock()
    mock_response.data = [1]
    mock_supabase_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_response
    result = await repository.delete_conjugations_by_verb(
        sample_db_conjugation.infinitive,
        sample_db_conjugation.auxiliary.value,
        sample_db_conjugation.reflexive,
    )
    assert result is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_verb_with_conjugations(
    repository, mock_supabase_client, sample_db_verb, sample_db_conjugation
):
    repository.get_verb_by_infinitive = AsyncMock(return_value=sample_db_verb)
    repository.get_conjugations = AsyncMock(return_value=[sample_db_conjugation])
    from src.schemas.verbs import VerbWithConjugations

    expected = VerbWithConjugations(
        **sample_db_verb.model_dump(), conjugations=[sample_db_conjugation]
    )
    result = await repository.get_verb_with_conjugations(
        sample_db_verb.infinitive,
        auxiliary=sample_db_verb.auxiliary.value,
        reflexive=sample_db_verb.reflexive,
        target_language_code=sample_db_verb.target_language_code,
    )
    assert result == expected


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "search_translation,query_chain",
    [
        (True, ["select", "or_", "limit"]),
        (False, ["select", "ilike", "limit"]),
    ],
)
async def test_search_verbs(
    repository, mock_supabase_client, sample_db_verb, search_translation, query_chain
):
    mock_response = MagicMock()
    mock_response.data = [sample_db_verb.model_dump()]
    # Setup the chain so that all chained calls return the same mock, and .execute is an AsyncMock
    async_execute = AsyncMock(return_value=mock_response)
    chain = MagicMock()
    for method in ["select", "or_", "ilike", "eq", "limit"]:
        setattr(chain, method, MagicMock(return_value=chain))
    chain.execute = async_execute
    mock_supabase_client.table.return_value = chain
    result = await repository.search_verbs(
        query="parl",
        search_translation=search_translation,
        target_language_code="eng",
        limit=5,
    )
    assert result[0].infinitive == sample_db_verb.infinitive


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_last_used(repository, mock_supabase_client, sample_db_verb):
    mock_response = MagicMock()
    mock_response.data = [1]
    mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response
    result = await repository.update_last_used(sample_db_verb.id)
    assert result is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upsert_conjugation_create(
    repository, mock_supabase_client, sample_conjugation_create, sample_db_conjugation
):
    repository.get_conjugation = AsyncMock(return_value=None)
    repository.create_conjugation = AsyncMock(return_value=sample_db_conjugation)
    await repository.upsert_conjugation(sample_conjugation_create)
    repository.create_conjugation.assert_awaited_once_with(sample_conjugation_create)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upsert_conjugation_update(
    repository, mock_supabase_client, sample_conjugation_create, sample_db_conjugation
):
    repository.get_conjugation = AsyncMock(return_value=sample_db_conjugation)
    repository.update_conjugation_by_verb_and_tense = AsyncMock()
    await repository.upsert_conjugation(sample_conjugation_create)
    repository.update_conjugation_by_verb_and_tense.assert_awaited()
