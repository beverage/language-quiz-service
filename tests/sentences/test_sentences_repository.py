"""Integration tests for the sentence repository using Supabase client."""

from uuid import uuid4

import pytest

from src.schemas.sentences import SentenceCreate, SentenceUpdate, Tense
from src.schemas.verbs import VerbCreate
from tests.sentences.fixtures import (
    generate_random_sentence_data,
    sentence_repository,  # noqa: F401
)
from tests.verbs.fixtures import (
    generate_random_verb_data,
    verb_repository,  # noqa: F401
)


class TestSentenceRepository:
    """Test class for sentence repository operations using Supabase client."""

    @pytest.fixture
    async def sample_verb_in_db(self, verb_repository):
        """Create a real verb in the database for sentence foreign key references."""
        verb_data = generate_random_verb_data()
        verb_create = VerbCreate(**verb_data)
        created_verb = await verb_repository.create_verb(verb_create)
        return created_verb

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_repository_with_client(self, sentence_repository):
        """Test creating repository with Supabase client."""
        assert sentence_repository.client is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_sentence(self, sentence_repository, sample_verb_in_db):
        """Test sentence creation using repository."""
        sentence_data = generate_random_sentence_data(verb_id=sample_verb_in_db.id)
        sentence_create = SentenceCreate(**sentence_data)

        result = await sentence_repository.create_sentence(sentence_create)

        assert result is not None
        assert result.id is not None
        assert result.verb_id == sample_verb_in_db.id
        assert result.content == sentence_create.content
        assert result.translation == sentence_create.translation
        assert result.target_language_code == sentence_create.target_language_code

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_sentence_failure_with_invalid_verb_id(
        self, sentence_repository
    ):
        """Test sentence creation failure with invalid verb ID."""
        sentence_data = generate_random_sentence_data(verb_id=uuid4())
        sentence_create = SentenceCreate(**sentence_data)

        with pytest.raises(Exception):  # Foreign key constraint violation
            await sentence_repository.create_sentence(sentence_create)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_sentence_by_id(self, sentence_repository, sample_verb_in_db):
        """Test retrieving sentence by ID using repository."""
        # Create sentence
        sentence_data = generate_random_sentence_data(verb_id=sample_verb_in_db.id)
        sentence_create = SentenceCreate(**sentence_data)
        created_sentence = await sentence_repository.create_sentence(sentence_create)

        # Retrieve sentence
        result = await sentence_repository.get_sentence(created_sentence.id)

        assert result is not None
        assert result.id == created_sentence.id
        assert result.content == created_sentence.content

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_sentence_not_found(self, sentence_repository):
        """Test retrieving non-existent sentence returns None."""
        result = await sentence_repository.get_sentence(uuid4())
        assert result is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_sentence(self, sentence_repository, sample_verb_in_db):
        """Test updating sentence using repository."""
        # Create sentence
        sentence_data = generate_random_sentence_data(verb_id=sample_verb_in_db.id)
        sentence_create = SentenceCreate(**sentence_data)
        created_sentence = await sentence_repository.create_sentence(sentence_create)

        # Update sentence
        update_data = SentenceUpdate(
            content="Updated content", translation="Updated translation"
        )
        result = await sentence_repository.update_sentence(
            created_sentence.id, update_data
        )

        assert result is not None
        assert result.id == created_sentence.id
        assert result.content == "Updated content"
        assert result.translation == "Updated translation"
        # Other fields should remain unchanged
        assert result.verb_id == created_sentence.verb_id

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_sentence_not_found(self, sentence_repository):
        """Test updating non-existent sentence returns None."""
        update_data = SentenceUpdate(content="New content")
        result = await sentence_repository.update_sentence(uuid4(), update_data)
        assert result is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_sentence(self, sentence_repository, sample_verb_in_db):
        """Test deleting sentence using repository."""
        # Create sentence
        sentence_data = generate_random_sentence_data(verb_id=sample_verb_in_db.id)
        sentence_create = SentenceCreate(**sentence_data)
        created_sentence = await sentence_repository.create_sentence(sentence_create)

        # Delete sentence
        result = await sentence_repository.delete_sentence(created_sentence.id)
        assert result is True

        # Verify deletion
        deleted_sentence = await sentence_repository.get_sentence(created_sentence.id)
        assert deleted_sentence is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_sentence_not_found(self, sentence_repository):
        """Test deleting non-existent sentence returns False."""
        result = await sentence_repository.delete_sentence(uuid4())
        assert result is False

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_sentences_basic(self, sentence_repository, sample_verb_in_db):
        """Test retrieving sentences list using repository."""
        # Create multiple sentences with unique content to avoid collision issues
        unique_suffix = uuid4().hex[:8]
        sentence_data_1 = generate_random_sentence_data(
            verb_id=sample_verb_in_db.id, content=f"Test sentence 1 {unique_suffix}"
        )
        sentence_data_2 = generate_random_sentence_data(
            verb_id=sample_verb_in_db.id, content=f"Test sentence 2 {unique_suffix}"
        )

        sentence1 = await sentence_repository.create_sentence(
            SentenceCreate(**sentence_data_1)
        )
        sentence2 = await sentence_repository.create_sentence(
            SentenceCreate(**sentence_data_2)
        )

        # Get sentences for this specific verb
        result = await sentence_repository.get_sentences(verb_id=sample_verb_in_db.id)

        assert len(result) >= 2
        sentence_ids = [s.id for s in result]
        assert sentence1.id in sentence_ids
        assert sentence2.id in sentence_ids

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_sentences_with_limit(
        self, sentence_repository, sample_verb_in_db
    ):
        """Test retrieving sentences with limit using repository."""
        # Create sentences
        for i in range(3):
            sentence_data = generate_random_sentence_data(
                verb_id=sample_verb_in_db.id,
                content=f"Limit test sentence {i} {uuid4().hex[:8]}",
            )
            await sentence_repository.create_sentence(SentenceCreate(**sentence_data))

        # Get sentences with limit for this verb
        result = await sentence_repository.get_sentences(
            verb_id=sample_verb_in_db.id, limit=2
        )

        assert len(result) == 2

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_sentences_with_is_correct_filter(
        self, sentence_repository, sample_verb_in_db
    ):
        """Test retrieving sentences filtered by is_correct using repository."""
        # Create correct and incorrect sentences
        unique_suffix = uuid4().hex[:8]
        correct_data = generate_random_sentence_data(
            verb_id=sample_verb_in_db.id,
            is_correct=True,
            content=f"Correct sentence {unique_suffix}",
        )
        incorrect_data = generate_random_sentence_data(
            verb_id=sample_verb_in_db.id,
            is_correct=False,
            content=f"Incorrect sentence {unique_suffix}",
        )

        correct_sentence = await sentence_repository.create_sentence(
            SentenceCreate(**correct_data)
        )
        await sentence_repository.create_sentence(SentenceCreate(**incorrect_data))

        # Get only correct sentences for this verb
        result = await sentence_repository.get_sentences(
            verb_id=sample_verb_in_db.id, is_correct=True
        )

        assert len(result) >= 1
        correct_ids = [s.id for s in result if s.is_correct]
        assert correct_sentence.id in correct_ids
        # Verify all returned sentences are correct
        for sentence in result:
            assert sentence.is_correct is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_sentences_with_tense_filter(
        self, sentence_repository, sample_verb_in_db
    ):
        """Test retrieving sentences filtered by tense using repository."""
        # Create sentences with different tenses
        unique_suffix = uuid4().hex[:8]
        present_data = generate_random_sentence_data(
            verb_id=sample_verb_in_db.id,
            tense=Tense.PRESENT,
            content=f"Present tense sentence {unique_suffix}",
        )
        past_data = generate_random_sentence_data(
            verb_id=sample_verb_in_db.id,
            tense=Tense.PASSE_COMPOSE,
            content=f"Past tense sentence {unique_suffix}",
        )

        present_sentence = await sentence_repository.create_sentence(
            SentenceCreate(**present_data)
        )
        await sentence_repository.create_sentence(SentenceCreate(**past_data))

        # Get only present tense sentences for this verb
        # Use enum.value for the filter
        result = await sentence_repository.get_sentences(
            verb_id=sample_verb_in_db.id, tense=Tense.PRESENT.value
        )

        assert len(result) >= 1
        present_ids = [s.id for s in result if s.tense == Tense.PRESENT]
        assert present_sentence.id in present_ids
        # Verify all returned sentences are present tense
        for sentence in result:
            assert sentence.tense == Tense.PRESENT

    @pytest.mark.parametrize(
        "operation,args,expected_result",
        [
            ("get_sentence", [uuid4()], None),
            ("update_sentence", [uuid4(), SentenceUpdate(content="test")], None),
            ("delete_sentence", [uuid4()], False),
        ],
    )
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_not_found_cases(
        self, sentence_repository, operation, args, expected_result
    ):
        """Test operations with non-existent resources using repository."""
        method = getattr(sentence_repository, operation)
        result = await method(*args)
        assert result == expected_result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_repository_error_handling_invalid_data(self, sentence_repository):
        """Test repository handles invalid data gracefully."""
        # Test with invalid enum values
        invalid_sentence_data = {
            "verb_id": uuid4(),  # This will fail FK constraint anyway
            "target_language_code": "fra",
            "content": "Test content",
            "translation": "Test translation",
            "tense": "INVALID_TENSE",  # Invalid enum
            "pronoun": "INVALID_PRONOUN",  # Invalid enum
            "is_correct": True,
        }

        with pytest.raises(Exception):  # Should raise validation or constraint error
            await sentence_repository.create_sentence(
                SentenceCreate(**invalid_sentence_data)
            )
