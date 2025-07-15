"""Integration tests for SentenceService.

Simple tests focused on business logic, using real repository connections.
No complex mocking - we trust the repository layer works with local Supabase.
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock

from src.services.sentence_service import SentenceService
from src.schemas.sentences import (
    SentenceCreate,
    SentenceUpdate,
    Pronoun,
    Tense,
    DirectObject,
    IndirectObject,
    Negation,
)
from src.schemas.verbs import VerbCreate
from tests.sentences.fixtures import generate_random_sentence_data
from tests.verbs.fixtures import generate_random_verb_data


@pytest.fixture
async def sentence_service(test_supabase_client):
    """Create a SentenceService with real repository connection."""
    from src.repositories.sentence_repository import SentenceRepository
    from src.services.verb_service import VerbService

    # Create repository with test client
    repo = SentenceRepository(client=test_supabase_client)

    # Create verb service with test client
    verb_service = VerbService()
    verb_service.db_client = test_supabase_client

    # Create service with real repository and verb service
    service = SentenceService(sentence_repository=repo, verb_service=verb_service)
    return service


@pytest.fixture
async def sample_verb(test_supabase_client):
    """Create a sample verb for sentence tests."""
    from src.services.verb_service import VerbService

    verb_service = VerbService()
    verb_service.db_client = test_supabase_client

    verb_data = VerbCreate(**generate_random_verb_data())
    return await verb_service.create_verb(verb_data)


@pytest.mark.asyncio
async def test_create_sentence(sentence_service, sample_verb):
    """Test creating a sentence."""
    sentence_data_dict = generate_random_sentence_data(verb_id=sample_verb.id)
    sentence_data = SentenceCreate(**sentence_data_dict)
    created_sentence = await sentence_service.create_sentence(sentence_data)

    assert created_sentence.content == sentence_data.content
    assert created_sentence.translation == sentence_data.translation
    assert created_sentence.verb_id == sample_verb.id


@pytest.mark.asyncio
async def test_get_sentence(sentence_service, sample_verb):
    """Test retrieving a sentence by ID."""
    # Create a sentence first
    sentence_data_dict = generate_random_sentence_data(verb_id=sample_verb.id)
    sentence_data = SentenceCreate(**sentence_data_dict)
    created_sentence = await sentence_service.create_sentence(sentence_data)

    # Retrieve it
    retrieved_sentence = await sentence_service.get_sentence(created_sentence.id)
    assert retrieved_sentence == created_sentence


@pytest.mark.asyncio
async def test_update_sentence(sentence_service, sample_verb):
    """Test updating a sentence."""
    # Create a sentence
    sentence_data_dict = generate_random_sentence_data(verb_id=sample_verb.id)
    sentence_data = SentenceCreate(**sentence_data_dict)
    created_sentence = await sentence_service.create_sentence(sentence_data)

    # Update it
    update_data = SentenceUpdate(
        content="updated content", translation="updated translation"
    )
    updated_sentence = await sentence_service.update_sentence(
        created_sentence.id, update_data
    )

    assert updated_sentence.content == "updated content"
    assert updated_sentence.translation == "updated translation"
    assert updated_sentence.verb_id == created_sentence.verb_id  # unchanged


@pytest.mark.asyncio
async def test_delete_sentence(sentence_service, sample_verb):
    """Test deleting a sentence."""
    # Create a sentence
    sentence_data_dict = generate_random_sentence_data(verb_id=sample_verb.id)
    sentence_data = SentenceCreate(**sentence_data_dict)
    created_sentence = await sentence_service.create_sentence(sentence_data)

    # Delete it
    result = await sentence_service.delete_sentence(created_sentence.id)
    assert result is True

    # Verify it's gone
    retrieved_sentence = await sentence_service.get_sentence(created_sentence.id)
    assert retrieved_sentence is None


@pytest.mark.asyncio
async def test_delete_nonexistent_sentence(sentence_service):
    """Test deleting a sentence that doesn't exist."""
    result = await sentence_service.delete_sentence(uuid4())
    assert result is False


@pytest.mark.asyncio
async def test_get_sentences_by_verb(sentence_service, sample_verb):
    """Test getting all sentences for a specific verb."""
    # Create multiple sentences for the verb
    sentences = []
    for i in range(3):
        sentence_data_dict = generate_random_sentence_data(verb_id=sample_verb.id)
        sentence_data_dict["content"] = f"Test sentence {i}"
        sentence_data = SentenceCreate(**sentence_data_dict)
        sentence = await sentence_service.create_sentence(sentence_data)
        sentences.append(sentence)

    # Get sentences by verb
    retrieved_sentences = await sentence_service.get_sentences_by_verb(sample_verb.id)

    assert len(retrieved_sentences) >= 3
    sentence_ids = {s.id for s in retrieved_sentences}
    for sentence in sentences:
        assert sentence.id in sentence_ids


@pytest.mark.asyncio
async def test_get_sentences_with_filters(sentence_service, sample_verb):
    """Test getting sentences with various filters."""
    # Create a sentence with specific properties
    unique_id = uuid4().hex[:8]

    correct_sentence_data_dict = generate_random_sentence_data(
        verb_id=sample_verb.id,
        is_correct=True,
        tense=Tense.PRESENT.value,
        content=f"Correct sentence {unique_id}",
    )
    correct_sentence_data = SentenceCreate(**correct_sentence_data_dict)
    correct_sentence = await sentence_service.create_sentence(correct_sentence_data)

    # Verify the sentence was created correctly
    assert correct_sentence.is_correct is True
    assert correct_sentence.tense == Tense.PRESENT

    # Test filtering - get sentences for this specific verb to narrow the results
    verb_sentences = await sentence_service.get_sentences_by_verb(sample_verb.id)
    assert len(verb_sentences) >= 1
    assert any(s.id == correct_sentence.id for s in verb_sentences)

    # Test filter by verb_id and correctness
    correct_sentences_for_verb = await sentence_service.get_sentences(
        verb_id=sample_verb.id, is_correct=True
    )
    assert any(s.id == correct_sentence.id for s in correct_sentences_for_verb)


@pytest.mark.asyncio
async def test_count_sentences(sentence_service, sample_verb):
    """Test counting sentences with filters."""
    # Create sentences with different properties
    for is_correct in [True, False]:
        sentence_data_dict = generate_random_sentence_data(
            verb_id=sample_verb.id, is_correct=is_correct
        )
        sentence_data = SentenceCreate(**sentence_data_dict)
        await sentence_service.create_sentence(sentence_data)

    # Count all sentences for the verb
    total_count = await sentence_service.count_sentences(verb_id=sample_verb.id)
    assert total_count >= 2

    # Count correct sentences for the verb
    correct_count = await sentence_service.count_sentences(
        verb_id=sample_verb.id, is_correct=True
    )
    assert correct_count >= 1

    # Count incorrect sentences for the verb
    incorrect_count = await sentence_service.count_sentences(
        verb_id=sample_verb.id, is_correct=False
    )
    assert incorrect_count >= 1


@pytest.mark.asyncio
async def test_get_random_sentence(sentence_service, sample_verb):
    """Test getting a random sentence."""
    # Create a sentence to ensure there's at least one
    sentence_data_dict = generate_random_sentence_data(verb_id=sample_verb.id)
    sentence_data = SentenceCreate(**sentence_data_dict)
    await sentence_service.create_sentence(sentence_data)

    # Get random sentence
    random_sentence = await sentence_service.get_random_sentence()
    assert random_sentence is not None

    # Get random sentence with filters
    random_correct = await sentence_service.get_random_sentence(is_correct=True)
    if random_correct:  # May be None if no correct sentences exist
        assert random_correct.is_correct is True


@pytest.mark.asyncio
async def test_get_all_sentences(sentence_service, sample_verb):
    """Test getting all sentences with limit."""
    # Create some sentences
    for i in range(3):
        sentence_data_dict = generate_random_sentence_data(verb_id=sample_verb.id)
        sentence_data = SentenceCreate(**sentence_data_dict)
        await sentence_service.create_sentence(sentence_data)

    # Get all sentences
    all_sentences = await sentence_service.get_all_sentences(limit=10)
    assert len(all_sentences) >= 3


# AI Integration Tests (with mocking)


@pytest.mark.asyncio
async def test_generate_sentence_success(sentence_service, sample_verb):
    """Test successful sentence generation with mocked AI."""
    # Mock the AI client and prompt generator
    mock_client = AsyncMock()
    mock_prompt_gen = AsyncMock()

    # Setup mocks
    mock_prompt_gen.generate_sentence_prompt.return_value = "sentence prompt"
    mock_client.handle_request.return_value = '{"sentence": "Je parle français", "translation": "I speak French", "is_correct": true, "has_compliment_object_direct": false, "has_compliment_object_indirect": false, "negation": "none"}'

    # Inject mocks
    sentence_service.openai_client = mock_client
    sentence_service.prompt_generator = mock_prompt_gen

    # Generate sentence
    result = await sentence_service.generate_sentence(
        verb_id=sample_verb.id,
        pronoun=Pronoun.FIRST_PERSON,
        tense=Tense.PRESENT,
        validate=False,  # Skip validation for simplicity
    )

    assert result.content == "Je parle français"
    assert result.translation == "I speak French"
    assert result.verb_id == sample_verb.id
    assert result.is_correct is True


@pytest.mark.asyncio
async def test_generate_sentence_with_validation(sentence_service, sample_verb):
    """Test sentence generation with validation enabled."""
    # Mock the AI client and prompt generator
    mock_client = AsyncMock()
    mock_prompt_gen = AsyncMock()

    # Setup mocks for both generation and validation
    mock_prompt_gen.generate_sentence_prompt.return_value = "sentence prompt"
    mock_prompt_gen.generate_correctness_prompt.return_value = "validation prompt"

    mock_client.handle_request.side_effect = [
        # First call: sentence generation
        '{"sentence": "Je parle français", "translation": "I speak French", "is_correct": true, "has_compliment_object_direct": false, "has_compliment_object_indirect": false, "negation": "none"}',
        # Second call: validation
        '{"is_valid": true, "explanation": "Sentence is correct", "actual_direct_object": "none", "actual_indirect_object": "none", "actual_negation": "none"}',
    ]

    # Inject mocks
    sentence_service.openai_client = mock_client
    sentence_service.prompt_generator = mock_prompt_gen

    # Generate sentence with validation
    result = await sentence_service.generate_sentence(
        verb_id=sample_verb.id,
        pronoun=Pronoun.FIRST_PERSON,
        tense=Tense.PRESENT,
        validate=True,
    )

    assert result.content == "Je parle français"
    assert result.translation == "I speak French"
    assert result.is_correct is True

    # Verify both generation and validation prompts were called
    assert mock_client.handle_request.call_count == 2


@pytest.mark.asyncio
async def test_generate_sentence_validation_failure(sentence_service, sample_verb):
    """Test sentence generation when validation fails."""
    # Mock the AI client and prompt generator
    mock_client = AsyncMock()
    mock_prompt_gen = AsyncMock()

    # Setup mocks
    mock_prompt_gen.generate_sentence_prompt.return_value = "sentence prompt"
    mock_prompt_gen.generate_correctness_prompt.return_value = "validation prompt"

    mock_client.handle_request.side_effect = [
        # First call: sentence generation
        '{"sentence": "Je parle français", "translation": "I speak French", "is_correct": true, "has_compliment_object_direct": false, "has_compliment_object_indirect": false, "negation": "none"}',
        # Second call: validation failure
        '{"is_valid": false, "explanation": "Grammar error detected", "actual_direct_object": "none", "actual_indirect_object": "none", "actual_negation": "none"}',
    ]

    # Inject mocks
    sentence_service.openai_client = mock_client
    sentence_service.prompt_generator = mock_prompt_gen

    # Generate sentence with validation - should raise error
    with pytest.raises(ValueError, match="Sentence validation failed"):
        await sentence_service.generate_sentence(
            verb_id=sample_verb.id,
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PRESENT,
            validate=True,
        )


@pytest.mark.asyncio
async def test_generate_sentence_nonexistent_verb(sentence_service):
    """Test sentence generation with non-existent verb."""
    with pytest.raises(ValueError, match="Verb with ID .* not found"):
        await sentence_service.generate_sentence(
            verb_id=uuid4(), pronoun=Pronoun.FIRST_PERSON, tense=Tense.PRESENT
        )
