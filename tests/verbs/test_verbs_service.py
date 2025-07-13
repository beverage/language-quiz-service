"""Unit tests for the Verb Service."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from src.services.verb_service import VerbService
from src.prompts.verb_prompts import VerbPromptGenerator
import json
import uuid
from datetime import datetime
from src.schemas.verbs import VerbCreate, VerbUpdate


def to_json_serializable(obj):
    if isinstance(obj, dict):
        return {k: to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_json_serializable(i) for i in obj]
    elif isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj


@pytest.fixture
def async_mock_verb_repository():
    repo = AsyncMock()
    repo.create_verb = AsyncMock()
    repo.get_verb = AsyncMock()
    repo.update_verb = AsyncMock()
    repo.delete_verb = AsyncMock()
    repo.get_verb_by_infinitive = AsyncMock()
    repo.get_verbs_by_infinitive = AsyncMock()
    repo.get_all_verbs = AsyncMock()
    repo.get_random_verb = AsyncMock()
    repo.update_last_used = AsyncMock()
    repo.delete_conjugations_by_verb = AsyncMock()
    repo.get_verb_with_conjugations = AsyncMock()
    repo.upsert_verb = AsyncMock()
    repo.upsert_conjugation = AsyncMock()
    repo.get_verb_with_conjugations_by_id = AsyncMock()
    repo.search_verbs = AsyncMock()
    repo.get_conjugations = AsyncMock()
    repo.update_conjugation_by_verb_and_tense = AsyncMock()
    return repo


@pytest.fixture
def async_mock_openai_client():
    client = AsyncMock()
    client.handle_request = AsyncMock()
    return client


@pytest.fixture
def async_mock_verb_prompt_generator():
    return MagicMock(spec=VerbPromptGenerator)


@pytest.fixture
def async_verb_service(
    monkeypatch,
    async_mock_verb_repository,
    async_mock_openai_client,
    async_mock_verb_prompt_generator,
):
    service = VerbService()
    monkeypatch.setattr(service, "openai_client", async_mock_openai_client)
    monkeypatch.setattr(
        service, "verb_prompt_generator", async_mock_verb_prompt_generator
    )
    monkeypatch.setattr(service, "verb_repository", async_mock_verb_repository)
    return service


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_case,setup_fn,expected_exception,expected_result",
    [
        (
            "success",
            lambda repo, ai, verb: (
                setattr(
                    ai,
                    'handle_request',
                    AsyncMock(return_value=json.dumps({
                        **to_json_serializable(VerbCreate(**verb.model_dump()).model_dump()),
                        "tenses": []
                    }))
                ),
                setattr(repo, 'upsert_verb', AsyncMock(return_value=verb)),
                setattr(repo, 'get_verb_with_conjugations_by_id', AsyncMock(return_value=verb))
            ),
            None,
            lambda verb: verb
        ),
        (
            "invalid_json",
            lambda repo, ai, verb: setattr(ai, 'handle_request', AsyncMock(return_value="not json")),
            ValueError,
            None
        ),
        (
            "validation_error",
            lambda repo, ai, verb: setattr(ai, 'handle_request', AsyncMock(return_value=json.dumps({"infinitive": "manger"}))),
            ValueError,
            None
        ),
        (
            "empty_response",
            lambda repo, ai, verb: setattr(ai, 'handle_request', AsyncMock(return_value="")),
            ValueError,
            None
        ),
    ]
)
async def test_download_verb_variants(async_verb_service, async_mock_openai_client, async_mock_verb_repository, sample_db_verb, test_case, setup_fn, expected_exception, expected_result):
    # Setup
    setup_fn(async_mock_verb_repository, async_mock_openai_client, sample_db_verb)
    verb_infinitive = sample_db_verb.infinitive
    if expected_exception:
        with pytest.raises(expected_exception):
            await async_verb_service.download_verb(verb_infinitive)
    else:
        result = await async_verb_service.download_verb(verb_infinitive)
        assert result == expected_result(sample_db_verb)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_verb(async_verb_service, async_mock_verb_repository, sample_verb_create, sample_db_verb):
    async_mock_verb_repository.create_verb.return_value = sample_db_verb
    result = await async_verb_service.create_verb(sample_verb_create)
    assert result == sample_db_verb
    async_mock_verb_repository.create_verb.assert_awaited_once_with(sample_verb_create)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_verb(async_verb_service, async_mock_verb_repository, sample_db_verb):
    async_mock_verb_repository.get_verb.return_value = sample_db_verb
    result = await async_verb_service.get_verb(sample_db_verb.id)
    assert result == sample_db_verb
    async_mock_verb_repository.get_verb.assert_awaited_once_with(sample_db_verb.id)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_verb_by_infinitive(async_verb_service, async_mock_verb_repository, sample_db_verb):
    async_mock_verb_repository.get_verb_by_infinitive.return_value = sample_db_verb
    result = await async_verb_service.get_verb_by_infinitive("parler", auxiliary="avoir", reflexive=False, target_language_code="eng")
    assert result == sample_db_verb
    async_mock_verb_repository.get_verb_by_infinitive.assert_awaited_once_with(
        infinitive="parler", auxiliary="avoir", reflexive=False, target_language_code="eng"
    )

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_verbs_by_infinitive(async_verb_service, async_mock_verb_repository, sample_db_verb):
    async_mock_verb_repository.get_verbs_by_infinitive.return_value = [sample_db_verb]
    result = await async_verb_service.get_verbs_by_infinitive("parler")
    assert result == [sample_db_verb]
    async_mock_verb_repository.get_verbs_by_infinitive.assert_awaited_once_with("parler")

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_all_verbs(async_verb_service, async_mock_verb_repository, sample_db_verb):
    async_mock_verb_repository.get_all_verbs.return_value = [sample_db_verb]
    result = await async_verb_service.get_all_verbs(limit=10, target_language_code="eng")
    assert result == [sample_db_verb]
    async_mock_verb_repository.get_all_verbs.assert_awaited_once_with(limit=10, target_language_code="eng")

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_random_verb(async_verb_service, async_mock_verb_repository, sample_db_verb):
    async_mock_verb_repository.get_random_verb.return_value = sample_db_verb
    async_mock_verb_repository.update_last_used.return_value = None
    result = await async_verb_service.get_random_verb(target_language_code="eng")
    assert result == sample_db_verb
    async_mock_verb_repository.get_random_verb.assert_awaited_once_with("eng")
    async_mock_verb_repository.update_last_used.assert_awaited_once_with(sample_db_verb.id)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_verb(async_verb_service, async_mock_verb_repository, sample_db_verb):
    update_data = VerbUpdate(infinitive="chanter", reflexive=True)
    updated_verb = sample_db_verb.model_copy(update={"infinitive": "chanter", "reflexive": True})
    async_mock_verb_repository.update_verb.return_value = updated_verb
    result = await async_verb_service.update_verb(sample_db_verb.id, update_data)
    assert result == updated_verb
    async_mock_verb_repository.update_verb.assert_awaited_once_with(sample_db_verb.id, update_data)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_verb(async_verb_service, async_mock_verb_repository, sample_db_verb):
    async_mock_verb_repository.get_verb.return_value = sample_db_verb
    async_mock_verb_repository.delete_conjugations_by_verb.return_value = True
    async_mock_verb_repository.delete_verb.return_value = True
    result = await async_verb_service.delete_verb(sample_db_verb.id)
    assert result is True
    async_mock_verb_repository.get_verb.assert_awaited_once_with(sample_db_verb.id)
    async_mock_verb_repository.delete_conjugations_by_verb.assert_awaited_once()
    async_mock_verb_repository.delete_verb.assert_awaited_once_with(sample_db_verb.id)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_verb_not_found(async_verb_service, async_mock_verb_repository):
    async_mock_verb_repository.get_verb.return_value = None
    result = await async_verb_service.delete_verb(uuid.uuid4())
    assert result is False

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_conjugations(async_verb_service, async_mock_verb_repository, sample_db_conjugation):
    async_mock_verb_repository.get_conjugations.return_value = [sample_db_conjugation]
    result = await async_verb_service.get_conjugations("parler", "avoir", False)
    assert result == [sample_db_conjugation]
    async_mock_verb_repository.get_conjugations.assert_awaited_once_with(infinitive="parler", auxiliary="avoir", reflexive=False)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_conjugations_by_verb_id(async_verb_service, async_mock_verb_repository, sample_db_verb, sample_db_conjugation):
    async_mock_verb_repository.get_verb.return_value = sample_db_verb
    async_mock_verb_repository.get_conjugations.return_value = [sample_db_conjugation]
    result = await async_verb_service.get_conjugations_by_verb_id(sample_db_verb.id)
    assert result == [sample_db_conjugation]
    async_mock_verb_repository.get_verb.assert_awaited_once_with(sample_db_verb.id)
    async_mock_verb_repository.get_conjugations.assert_awaited_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_conjugations_by_verb_id_not_found(async_verb_service, async_mock_verb_repository):
    async_mock_verb_repository.get_verb.return_value = None
    result = await async_verb_service.get_conjugations_by_verb_id(uuid.uuid4())
    assert result == []

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_conjugation(async_verb_service, async_mock_verb_repository, sample_conjugation_create, sample_db_conjugation):
    async_mock_verb_repository.create_conjugation.return_value = sample_db_conjugation
    result = await async_verb_service.create_conjugation(sample_conjugation_create)
    assert result == sample_db_conjugation
    async_mock_verb_repository.create_conjugation.assert_awaited_once_with(sample_conjugation_create)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_conjugation(async_verb_service, async_mock_verb_repository, sample_db_conjugation):
    from src.schemas.verbs import ConjugationUpdate, Tense
    update_data = ConjugationUpdate(first_person_singular="nouvelle forme")
    updated_conjugation = sample_db_conjugation.model_copy(update={"first_person_singular": "nouvelle forme"})
    async_mock_verb_repository.update_conjugation_by_verb_and_tense.return_value = updated_conjugation
    result = await async_verb_service.update_conjugation(
        sample_db_conjugation.infinitive,
        sample_db_conjugation.auxiliary.value,
        sample_db_conjugation.reflexive,
        sample_db_conjugation.tense,
        update_data
    )
    assert result == updated_conjugation
    async_mock_verb_repository.update_conjugation_by_verb_and_tense.assert_awaited_once_with(
        infinitive=sample_db_conjugation.infinitive,
        auxiliary=sample_db_conjugation.auxiliary.value,
        reflexive=sample_db_conjugation.reflexive,
        tense=sample_db_conjugation.tense,
        conjugation=update_data
    )

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_verb_with_conjugations(async_verb_service, async_mock_verb_repository, sample_db_verb):
    from src.schemas.verbs import VerbWithConjugations
    async_mock_verb_repository.get_verbs_by_infinitive.return_value = [sample_db_verb]
    expected = VerbWithConjugations(**sample_db_verb.model_dump(), conjugations=[])
    async_mock_verb_repository.get_verb_with_conjugations.return_value = expected
    result = await async_verb_service.get_verb_with_conjugations(
        sample_db_verb.infinitive,
        auxiliary=sample_db_verb.auxiliary.value,
        reflexive=sample_db_verb.reflexive,
        target_language_code=sample_db_verb.target_language_code
    )
    assert result == expected
    async_mock_verb_repository.get_verb_with_conjugations.assert_awaited_once_with(
        infinitive=sample_db_verb.infinitive,
        auxiliary=sample_db_verb.auxiliary.value,
        reflexive=sample_db_verb.reflexive,
        target_language_code=sample_db_verb.target_language_code
    )

@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_verbs(async_verb_service, async_mock_verb_repository, sample_db_verb):
    async_mock_verb_repository.search_verbs.return_value = [sample_db_verb]
    result = await async_verb_service.search_verbs(query="parl", search_translation=True, target_language_code="eng", limit=5)
    assert result == [sample_db_verb]
    async_mock_verb_repository.search_verbs.assert_awaited_once_with(
        query="parl", search_translation=True, target_language_code="eng", limit=5
    )
