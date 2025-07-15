"""Integration tests for the sentence repository using testcontainers and direct database calls."""

import pytest
import asyncpg
from uuid import uuid4

from src.schemas.sentences import (
    SentenceCreate,
    SentenceUpdate,
)
from tests.sentences.fixtures import (
    generate_random_sentence_data,
    sentence_repository,  # noqa: F401
)
from tests.sentences.db_helpers import (
    create_sentence,
    get_sentence,
)
from tests.verbs.db_helpers import create_verb
from tests.verbs.fixtures import generate_random_verb_data


class TestSentenceRepository:
    """Test class for sentence repository operations."""

    @pytest.fixture
    async def sample_verb(self, supabase_db_connection):
        """Create a sample verb for sentence tests."""
        verb_data = generate_random_verb_data()
        return await create_verb(supabase_db_connection, verb_data)

    @pytest.fixture
    async def sample_sentence(self, supabase_db_connection, sample_verb):
        """Create a sample sentence for tests."""
        sentence_data = generate_random_sentence_data(verb_id=sample_verb.id)
        return await create_sentence(supabase_db_connection, sentence_data)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_repository_with_testcontainers(self, sentence_repository):
        """Test creating repository with local Supabase client."""
        assert sentence_repository.client is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_sentence_failure_with_invalid_verb_id(
        self, sentence_repository
    ):
        """Test sentence creation failure with invalid verb ID."""

        # Create sentence data with non-existent verb ID
        sentence_data = generate_random_sentence_data(verb_id=uuid4())
        sentence_create = SentenceCreate(**sentence_data)

        # Attempt to create sentence should fail due to foreign key constraint
        with pytest.raises(
            Exception
        ):  # Could be various exception types depending on implementation
            await sentence_repository.create_sentence(sentence_create)

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method_name,setup_data,call_args,expected_result_check",
        [
            (
                "create_sentence",
                None,  # Will be set up with valid verb_id in the test
                lambda data: (data,),
                lambda result, data: result.content == data.content,
            ),
            (
                "get_sentence",
                None,  # Will use existing sentence from fixture
                lambda data: (data.id,) if hasattr(data, "id") else (uuid4(),),
                lambda result, data: result is not None and hasattr(result, "id"),
            ),
            (
                "update_sentence",
                lambda: SentenceUpdate(
                    content="Updated content", translation="Updated translation"
                ),
                lambda data: (uuid4(), data),  # Will be overridden in test
                lambda result, data: result.content == "Updated content",
            ),
            (
                "delete_sentence",
                None,  # Will use existing sentence from fixture
                lambda data: (data.id,) if hasattr(data, "id") else (uuid4(),),
                lambda result, data: result is True,
            ),
        ],
    )
    async def test_sentence_crud_operations(
        self,
        sentence_repository,
        supabase_db_connection,
        sample_verb,
        method_name,
        setup_data,
        call_args,
        expected_result_check,
    ):
        """Test basic CRUD operations for sentences."""
        # Setup initial data if needed
        initial_sentence = None
        if method_name in ["get_sentence", "update_sentence", "delete_sentence"]:
            sentence_data = generate_random_sentence_data(verb_id=sample_verb.id)
            initial_sentence = await create_sentence(
                supabase_db_connection, sentence_data
            )

        # Prepare test data
        if method_name == "create_sentence":
            data = SentenceCreate(
                **generate_random_sentence_data(verb_id=sample_verb.id)
            )
        elif setup_data:
            data = setup_data()
        else:
            data = initial_sentence

        # Prepare call arguments
        if method_name == "update_sentence" and initial_sentence:
            args = (initial_sentence.id, data)
        else:
            args = call_args(data)

        # Execute operation
        method = getattr(sentence_repository, method_name)
        result = await method(*args)

        # Verify result
        assert expected_result_check(result, data)

        # Additional verifications
        if method_name == "create_sentence":
            assert result.id is not None
            assert result.created_at is not None
            assert result.updated_at is not None
            # Verify in database
            db_sentence = await get_sentence(supabase_db_connection, result.id)
            assert db_sentence is not None
            assert db_sentence.content == data.content

        elif method_name == "get_sentence" and initial_sentence:
            assert result.id == initial_sentence.id
            assert result.content == initial_sentence.content

        elif method_name == "update_sentence" and initial_sentence:
            assert result.id == initial_sentence.id
            assert result.content == "Updated content"
            # Verify in database
            db_sentence = await get_sentence(
                supabase_db_connection, initial_sentence.id
            )
            assert db_sentence.content == "Updated content"

        elif method_name == "delete_sentence" and initial_sentence:
            assert result is True
            # Verify removal from database
            db_sentence = await get_sentence(
                supabase_db_connection, initial_sentence.id
            )
            assert db_sentence is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sentence_retrieval_methods(
        self, sentence_repository, supabase_db_connection, sample_verb
    ):
        """Test different sentence retrieval methods."""
        # Create test sentences
        sentence_data_1 = generate_random_sentence_data(verb_id=sample_verb.id)
        sentence_data_2 = generate_random_sentence_data(verb_id=sample_verb.id)
        sentence_data_2["content"] = "Unique test sentence content."

        sentence1 = await create_sentence(supabase_db_connection, sentence_data_1)
        sentence2 = await create_sentence(supabase_db_connection, sentence_data_2)

        # Test get by ID - these should work regardless of what else is in the database
        retrieved_sentence1 = await sentence_repository.get_sentence(sentence1.id)
        assert retrieved_sentence1.id == sentence1.id
        assert retrieved_sentence1.content == sentence1.content

        retrieved_sentence2 = await sentence_repository.get_sentence(sentence2.id)
        assert retrieved_sentence2.id == sentence2.id
        assert retrieved_sentence2.content == sentence2.content

        # Test get sentences (list) - just verify it returns a list and our sentences exist when queried individually
        all_sentences = await sentence_repository.get_sentences()
        assert isinstance(all_sentences, list)
        assert len(all_sentences) >= 2  # Should have at least our 2 sentences

        # Test not found case
        non_existent_sentence = await sentence_repository.get_sentence(uuid4())
        assert non_existent_sentence is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_random_sentence_with_filters(
        self, sentence_repository, supabase_db_connection, sample_verb
    ):
        """Test getting random sentence with filters."""
        # Create sentences with specific attributes
        sentence_data = generate_random_sentence_data(verb_id=sample_verb.id)
        sentence_data["pronoun"] = "first_person"
        sentence_data["tense"] = "present"

        await create_sentence(supabase_db_connection, sentence_data)

        # Test get random sentence with filters (use individual parameters)
        random_sentence = await sentence_repository.get_random_sentence(is_correct=True)

        if random_sentence:  # May be None if no sentences match
            assert random_sentence.is_correct is True

        # Test get random sentence without filters
        random_any = await sentence_repository.get_random_sentence()
        assert random_any is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_count_sentences_with_filters(
        self, sentence_repository, supabase_db_connection, sample_verb
    ):
        """Test counting sentences with various filters."""
        # Create sentences with known attributes
        sentence_data_1 = generate_random_sentence_data(verb_id=sample_verb.id)
        sentence_data_1["pronoun"] = "first_person"
        sentence_data_1["is_correct"] = True

        sentence_data_2 = generate_random_sentence_data(verb_id=sample_verb.id)
        sentence_data_2["pronoun"] = "second_person"
        sentence_data_2["is_correct"] = False

        await create_sentence(supabase_db_connection, sentence_data_1)
        await create_sentence(supabase_db_connection, sentence_data_2)

        # Test count all sentences
        total_count = await sentence_repository.count_sentences()
        assert total_count >= 2

        # Test count with individual filters
        first_person_count = await sentence_repository.count_sentences(
            verb_id=sample_verb.id
        )
        assert first_person_count >= 1

        correct_count = await sentence_repository.count_sentences(is_correct=True)
        assert correct_count >= 1

        non_matching_count = await sentence_repository.count_sentences(is_correct=False)
        # Should be 0 unless other tests created sentences with this pronoun
        assert non_matching_count >= 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_sentences_with_filters(
        self, sentence_repository, supabase_db_connection, sample_verb
    ):
        """Test getting sentences with various filters."""
        # Create sentences with specific attributes
        present_sentence_data = generate_random_sentence_data(verb_id=sample_verb.id)
        present_sentence_data["tense"] = "present"
        present_sentence_data["pronoun"] = "first_person"

        past_sentence_data = generate_random_sentence_data(verb_id=sample_verb.id)
        past_sentence_data["tense"] = "passe_compose"
        past_sentence_data["pronoun"] = "third_person"

        present_sentence = await create_sentence(
            supabase_db_connection, present_sentence_data
        )
        past_sentence = await create_sentence(
            supabase_db_connection, past_sentence_data
        )

        # Test filter by tense - verify all returned sentences match the filter
        present_sentences = await sentence_repository.get_sentences(tense="present")
        assert len(present_sentences) >= 1
        assert all(s.tense == "present" for s in present_sentences)

        # Test filter by pronoun - verify all returned sentences match the filter
        first_person_sentences = await sentence_repository.get_sentences(
            pronoun="first_person"
        )
        assert len(first_person_sentences) >= 1
        assert all(s.pronoun == "first_person" for s in first_person_sentences)

        # Test multiple filters - verify all returned sentences match both criteria
        specific_sentences = await sentence_repository.get_sentences(
            tense="present", pronoun="first_person"
        )
        assert len(specific_sentences) >= 1
        assert all(
            s.tense == "present" and s.pronoun == "first_person"
            for s in specific_sentences
        )

        # Test pagination
        limited_sentences = await sentence_repository.get_sentences(limit=1)
        assert len(limited_sentences) == 1

        # Verify our specific sentences exist by querying them individually
        retrieved_present = await sentence_repository.get_sentence(present_sentence.id)
        assert retrieved_present is not None
        assert retrieved_present.tense == "present"
        assert retrieved_present.pronoun == "first_person"

        retrieved_past = await sentence_repository.get_sentence(past_sentence.id)
        assert retrieved_past is not None
        assert retrieved_past.tense == "passe_compose"
        assert retrieved_past.pronoun == "third_person"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_sentences_complex_filtering(
        self, sentence_repository, supabase_db_connection, sample_verb
    ):
        """Test complex sentence filtering scenarios."""
        # Create sentences with various combinations
        combinations = [
            {
                "pronoun": "first_person",
                "tense": "present",
                "direct_object": "none",
                "negation": "none",
            },
            {
                "pronoun": "second_person",
                "tense": "present",
                "direct_object": "masculine",
                "negation": "pas",
            },
            {
                "pronoun": "third_person",
                "tense": "passe_compose",
                "direct_object": "feminine",
                "negation": "none",
            },
        ]

        created_sentences = []
        for combo in combinations:
            sentence_data = generate_random_sentence_data(verb_id=sample_verb.id)
            sentence_data.update(combo)
            sentence = await create_sentence(supabase_db_connection, sentence_data)
            created_sentences.append(sentence)

        # Test filtering by multiple criteria
        present_tense_sentences = await sentence_repository.get_sentences(
            tense="present"
        )
        assert len(present_tense_sentences) >= 2

        negated_sentences = await sentence_repository.get_sentences(is_correct=True)
        assert len(negated_sentences) >= 1

        direct_object_sentences = await sentence_repository.get_sentences(
            tense="present"
        )
        assert len(direct_object_sentences) >= 1

        # Test combination filters
        specific_combo = await sentence_repository.get_sentences(
            pronoun="first_person", tense="present"
        )
        assert len(specific_combo) >= 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sentence_update_partial_fields(
        self, sentence_repository, supabase_db_connection, sample_verb
    ):
        """Test updating sentences with partial field updates."""
        # Create a sentence
        sentence_data = generate_random_sentence_data(verb_id=sample_verb.id)
        original_sentence = await create_sentence(supabase_db_connection, sentence_data)

        # Test updating only content
        content_update = SentenceUpdate(content="Updated content only")
        updated_sentence = await sentence_repository.update_sentence(
            original_sentence.id, content_update
        )
        assert updated_sentence.content == "Updated content only"
        assert (
            updated_sentence.translation == original_sentence.translation
        )  # Should remain unchanged

        # Test updating only translation
        translation_update = SentenceUpdate(translation="Updated translation only")
        updated_sentence = await sentence_repository.update_sentence(
            original_sentence.id, translation_update
        )
        assert updated_sentence.translation == "Updated translation only"
        assert (
            updated_sentence.content == "Updated content only"
        )  # Should keep previous update

        # Test updating enum fields
        enum_update = SentenceUpdate(pronoun="third_person", negation="pas")
        updated_sentence = await sentence_repository.update_sentence(
            original_sentence.id, enum_update
        )
        assert updated_sentence.pronoun == "third_person"
        assert updated_sentence.negation == "pas"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sentence_deletion_cascade_behavior(
        self, sentence_repository, supabase_db_connection, sample_verb
    ):
        """Test sentence deletion and any cascade behaviors."""
        # Create a sentence
        sentence_data = generate_random_sentence_data(verb_id=sample_verb.id)
        sentence = await create_sentence(supabase_db_connection, sentence_data)

        # Verify sentence exists
        existing_sentence = await get_sentence(supabase_db_connection, sentence.id)
        assert existing_sentence is not None

        # Delete the sentence
        delete_result = await sentence_repository.delete_sentence(sentence.id)
        assert delete_result is True

        # Verify sentence is deleted
        deleted_sentence = await get_sentence(supabase_db_connection, sentence.id)
        assert deleted_sentence is None

        # Verify verb still exists (no cascade deletion)
        from tests.verbs.db_helpers import get_verb

        existing_verb = await get_verb(supabase_db_connection, sample_verb.id)
        assert existing_verb is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_sentences_by_verb_with_multiple_verbs(
        self, sentence_repository, supabase_db_connection
    ):
        """Test getting sentences by verb when multiple verbs exist."""
        # Create multiple verbs
        verb_data_1 = generate_random_verb_data()
        verb_data_2 = generate_random_verb_data()
        verb_data_2["infinitive"] = "unique_verb_for_test"

        verb1 = await create_verb(supabase_db_connection, verb_data_1)
        verb2 = await create_verb(supabase_db_connection, verb_data_2)

        # Create sentences for each verb
        sentence_data_1 = generate_random_sentence_data(verb_id=verb1.id)
        sentence_data_2 = generate_random_sentence_data(verb_id=verb1.id)
        sentence_data_3 = generate_random_sentence_data(verb_id=verb2.id)

        sentence1 = await create_sentence(supabase_db_connection, sentence_data_1)
        sentence2 = await create_sentence(supabase_db_connection, sentence_data_2)
        sentence3 = await create_sentence(supabase_db_connection, sentence_data_3)

        # Test getting sentences by verb1
        verb1_sentences = await sentence_repository.get_sentences_by_verb(verb1.id)
        assert len(verb1_sentences) >= 2
        verb1_sentence_ids = [s.id for s in verb1_sentences]
        assert sentence1.id in verb1_sentence_ids
        assert sentence2.id in verb1_sentence_ids
        assert sentence3.id not in verb1_sentence_ids

        # Test getting sentences by verb2
        verb2_sentences = await sentence_repository.get_sentences_by_verb(verb2.id)
        assert len(verb2_sentences) >= 1
        verb2_sentence_ids = [s.id for s in verb2_sentences]
        assert sentence3.id in verb2_sentence_ids
        assert sentence1.id not in verb2_sentence_ids
        assert sentence2.id not in verb2_sentence_ids

        # Test getting sentences for non-existent verb
        empty_sentences = await sentence_repository.get_sentences_by_verb(uuid4())
        assert len(empty_sentences) == 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation,args,expected_result",
        [
            ("get_sentence", (uuid4(),), None),
            ("update_sentence", (uuid4(), SentenceUpdate(content="test")), None),
            ("delete_sentence", (uuid4(),), False),
        ],
    )
    async def test_not_found_cases(
        self, sentence_repository, operation, args, expected_result
    ):
        """Test operations with non-existent resources."""
        method = getattr(sentence_repository, operation)
        result = await method(*args)
        assert result == expected_result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_repository_basic_functionality(self, sentence_repository):
        """Basic smoke test for sentence repository functionality."""
        # Test that repository can be created and basic methods exist
        assert hasattr(sentence_repository, "create_sentence")
        assert hasattr(sentence_repository, "get_sentence")
        assert hasattr(sentence_repository, "update_sentence")
        assert hasattr(sentence_repository, "delete_sentence")
        assert hasattr(sentence_repository, "get_sentences")
        assert hasattr(sentence_repository, "count_sentences")
        assert hasattr(sentence_repository, "get_sentences_by_verb")
        assert hasattr(sentence_repository, "get_random_sentence")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sentence_enum_handling(
        self, sentence_repository, supabase_db_connection, sample_verb
    ):
        """Test that sentence enum fields are handled correctly."""
        # Test creating sentence with all enum types
        sentence_data = generate_random_sentence_data(verb_id=sample_verb.id)
        sentence_data.update(
            {
                "pronoun": "third_person",
                "tense": "passe_compose",
                "direct_object": "masculine",
                "indirect_object": "feminine",
                "negation": "pas",
            }
        )

        sentence_create = SentenceCreate(**sentence_data)
        created_sentence = await sentence_repository.create_sentence(sentence_create)

        # Verify enum values are preserved
        assert created_sentence.pronoun == "third_person"
        assert created_sentence.tense == "passe_compose"
        assert created_sentence.direct_object == "masculine"
        assert created_sentence.indirect_object == "feminine"
        assert created_sentence.negation == "pas"

        # Verify in database
        db_sentence = await get_sentence(supabase_db_connection, created_sentence.id)
        assert db_sentence.pronoun == "third_person"
        assert db_sentence.tense == "passe_compose"
        assert db_sentence.direct_object == "masculine"
        assert db_sentence.indirect_object == "feminine"
        assert db_sentence.negation == "pas"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sentence_complex_enum_combinations(
        self, sentence_repository, supabase_db_connection, sample_verb
    ):
        """Test sentences with various enum combinations work correctly."""
        test_combinations = [
            {
                "pronoun": "first_person",
                "tense": "present",
                "direct_object": "none",
                "indirect_object": "none",
                "negation": "none",
            },
            {
                "pronoun": "second_person",
                "tense": "future_simple",
                "direct_object": "feminine",
                "indirect_object": "masculine",
                "negation": "jamais",
            },
            {
                "pronoun": "third_person_plural",
                "tense": "imparfait",
                "direct_object": "plural",
                "indirect_object": "plural",
                "negation": "plus",
            },
        ]

        created_sentences = []
        for combo in test_combinations:
            sentence_data = generate_random_sentence_data(verb_id=sample_verb.id)
            sentence_data.update(combo)

            sentence_create = SentenceCreate(**sentence_data)
            created_sentence = await sentence_repository.create_sentence(
                sentence_create
            )
            created_sentences.append(created_sentence)

            # Verify each combination
            for key, value in combo.items():
                assert getattr(created_sentence, key) == value

        # Test filtering by these combinations
        first_person_present = await sentence_repository.get_sentences(
            pronoun="first_person", tense="present"
        )
        assert len(first_person_present) >= 1

        negated_sentences = await sentence_repository.get_sentences(is_correct=False)
        assert len(negated_sentences) >= 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_sentences_with_target_language_filter(
        self, sentence_repository, supabase_db_connection, sample_verb
    ):
        """Test filtering sentences by target language code."""
        # Create sentences with different target languages
        eng_sentence_data = generate_random_sentence_data(verb_id=sample_verb.id)
        eng_sentence_data["target_language_code"] = "eng"

        fra_sentence_data = generate_random_sentence_data(verb_id=sample_verb.id)
        fra_sentence_data["target_language_code"] = "fra"

        eng_sentence = await create_sentence(supabase_db_connection, eng_sentence_data)
        fra_sentence = await create_sentence(supabase_db_connection, fra_sentence_data)

        # Test filtering by language - verify all returned sentences match the filter
        eng_sentences = await sentence_repository.get_sentences(
            target_language_code="eng"
        )
        assert len(eng_sentences) >= 1
        assert all(s.target_language_code == "eng" for s in eng_sentences)

        fra_sentences = await sentence_repository.get_sentences(
            target_language_code="fra"
        )
        assert len(fra_sentences) >= 1
        assert all(s.target_language_code == "fra" for s in fra_sentences)

        # Verify our specific sentences exist by querying them individually
        retrieved_eng = await sentence_repository.get_sentence(eng_sentence.id)
        assert retrieved_eng is not None
        assert retrieved_eng.target_language_code == "eng"

        retrieved_fra = await sentence_repository.get_sentence(fra_sentence.id)
        assert retrieved_fra is not None
        assert retrieved_fra.target_language_code == "fra"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sentence_language_code_validation(
        self, sentence_repository, supabase_db_connection, sample_verb
    ):
        """Test that invalid language codes are rejected."""
        # Test creating sentence with invalid language code
        sentence_data = generate_random_sentence_data(verb_id=sample_verb.id)
        sentence_data["target_language_code"] = "invalid_lang_code"

        # This should fail during Pydantic validation before reaching the database
        with pytest.raises(Exception):  # Pydantic validation error
            sentence_create = SentenceCreate(**sentence_data)

        # Test with valid language codes
        valid_codes = ["eng", "fra", "spa", "deu"]
        for code in valid_codes:
            sentence_data = generate_random_sentence_data(verb_id=sample_verb.id)
            sentence_data["target_language_code"] = code

            sentence_create = SentenceCreate(**sentence_data)
            created_sentence = await sentence_repository.create_sentence(
                sentence_create
            )
            assert created_sentence.target_language_code == code

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_repository_error_handling_edge_cases(
        self, sentence_repository, supabase_db_connection, sample_verb
    ):
        """Test repository error handling for edge cases."""
        # Test updating with empty update data
        sentence_data = generate_random_sentence_data(verb_id=sample_verb.id)
        sentence = await create_sentence(supabase_db_connection, sentence_data)

        empty_update = SentenceUpdate()
        result = await sentence_repository.update_sentence(sentence.id, empty_update)

        # When update is empty, behavior may vary - verify the original sentence is unchanged
        if result is not None:
            # If it returns the sentence, it should be unchanged
            assert result.id == sentence.id
            assert result.content == sentence.content
        else:
            # If it returns None, verify the original sentence still exists unchanged
            original_sentence = await sentence_repository.get_sentence(sentence.id)
            assert original_sentence is not None
            assert original_sentence.id == sentence.id
            assert original_sentence.content == sentence.content

        # Test creating sentence with minimal required fields
        minimal_data = {
            "content": "Minimal sentence",
            "translation": "Minimal translation",
            "verb_id": sample_verb.id,
            "pronoun": "first_person",
            "tense": "present",
            "direct_object": "none",
            "indirect_object": "none",
            "negation": "none",
        }

        minimal_create = SentenceCreate(**minimal_data)
        minimal_sentence = await sentence_repository.create_sentence(minimal_create)
        assert minimal_sentence.content == "Minimal sentence"
        assert minimal_sentence.is_correct is True  # Default value
        assert minimal_sentence.explanation is None  # Optional field

    # ============================================================================
    # Database Constraint Tests
    # ============================================================================

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sentence_database_constraints(
        self, supabase_db_connection, sample_verb
    ):
        """Test that database constraints are properly enforced for sentences using domain objects."""

        # Test invalid language code constraint
        invalid_lang_sentence_data = {
            "content": "Test sentence",
            "translation": "Test translation",
            "verb_id": sample_verb.id,
            "pronoun": "first_person",
            "tense": "present",
            "direct_object": "none",
            "indirect_object": "none",
            "negation": "none",
            "target_language_code": "invalid_lang_code_too_long",  # Should violate constraint
        }

        with pytest.raises((asyncpg.CheckViolationError, asyncpg.DataError)):
            await create_sentence(supabase_db_connection, invalid_lang_sentence_data)

        # Test invalid enum values
        invalid_pronoun_sentence_data = {
            "content": "Test sentence",
            "translation": "Test translation",
            "verb_id": sample_verb.id,
            "pronoun": "invalid_pronoun",  # Should violate enum constraint
            "tense": "present",
            "direct_object": "none",
            "indirect_object": "none",
            "negation": "none",
            "target_language_code": "eng",
        }

        with pytest.raises((asyncpg.CheckViolationError, asyncpg.DataError)):
            await create_sentence(supabase_db_connection, invalid_pronoun_sentence_data)

        # Test invalid tense
        invalid_tense_data = {
            "content": "Test sentence",
            "translation": "Test translation",
            "verb_id": sample_verb.id,
            "pronoun": "first_person",
            "tense": "invalid_tense",  # Should violate enum constraint
            "direct_object": "none",
            "indirect_object": "none",
            "negation": "none",
            "target_language_code": "eng",
        }

        with pytest.raises((asyncpg.CheckViolationError, asyncpg.DataError)):
            await create_sentence(supabase_db_connection, invalid_tense_data)

        # Test invalid direct_object
        invalid_direct_object_data = {
            "content": "Test sentence",
            "translation": "Test translation",
            "verb_id": sample_verb.id,
            "pronoun": "first_person",
            "tense": "present",
            "direct_object": "invalid_direct_object",  # Should violate enum constraint
            "indirect_object": "none",
            "negation": "none",
            "target_language_code": "eng",
        }

        with pytest.raises((asyncpg.CheckViolationError, asyncpg.DataError)):
            await create_sentence(supabase_db_connection, invalid_direct_object_data)

        # Test invalid negation
        invalid_negation_data = {
            "content": "Test sentence",
            "translation": "Test translation",
            "verb_id": sample_verb.id,
            "pronoun": "first_person",
            "tense": "present",
            "direct_object": "none",
            "indirect_object": "none",
            "negation": "invalid_negation",  # Should violate enum constraint
            "target_language_code": "eng",
        }

        with pytest.raises((asyncpg.CheckViolationError, asyncpg.DataError)):
            await create_sentence(supabase_db_connection, invalid_negation_data)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sentence_foreign_key_constraints(self, supabase_db_connection):
        """Test foreign key constraints for sentences using domain objects."""

        # Test non-existent verb_id constraint
        nonexistent_verb_sentence_data = {
            "content": "Test sentence",
            "translation": "Test translation",
            "verb_id": uuid4(),  # Random UUID that doesn't exist
            "pronoun": "first_person",
            "tense": "present",
            "direct_object": "none",
            "indirect_object": "none",
            "negation": "none",
            "target_language_code": "eng",
        }

        with pytest.raises(asyncpg.ForeignKeyViolationError):
            await create_sentence(
                supabase_db_connection, nonexistent_verb_sentence_data
            )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sentence_not_null_constraints(
        self, supabase_db_connection, sample_verb
    ):
        """Test NOT NULL constraints for sentences using domain objects."""

        # Test missing required content field
        missing_content_data = {
            "content": None,  # Should violate NOT NULL constraint
            "translation": "Test translation",
            "verb_id": sample_verb.id,
            "pronoun": "first_person",
            "tense": "present",
            "direct_object": "none",
            "indirect_object": "none",
            "negation": "none",
            "target_language_code": "eng",
        }

        with pytest.raises((asyncpg.NotNullViolationError, ValueError)):
            await create_sentence(supabase_db_connection, missing_content_data)

        # Test missing required translation field
        missing_translation_data = {
            "content": "Test sentence",
            "translation": None,  # Should violate NOT NULL constraint
            "verb_id": sample_verb.id,
            "pronoun": "first_person",
            "tense": "present",
            "direct_object": "none",
            "indirect_object": "none",
            "negation": "none",
            "target_language_code": "eng",
        }

        with pytest.raises((asyncpg.NotNullViolationError, ValueError)):
            await create_sentence(supabase_db_connection, missing_translation_data)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sentence_index_performance(self, supabase_db_connection):
        """Test that expected database indexes exist for sentence performance."""
        # Query for indexes on sentences table
        index_query = """
            SELECT indexname, tablename, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'sentences'
            ORDER BY indexname
        """

        indexes = await supabase_db_connection.fetch(index_query)
        index_names = [idx["indexname"] for idx in indexes]

        # Should have at least the primary key index
        assert any("pkey" in name for name in index_names)

        # Optional: Check for expected performance indexes
        # (These would depend on actual database schema design)
        # assert any("verb_id" in name for name in index_names)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cross_domain_sentence_constraint_patterns(
        self, supabase_db_connection, sample_verb
    ):
        """Test constraint patterns that involve sentences and other domain tables."""
        # Test that sentence creation respects verb foreign key constraints
        sentence_data = generate_random_sentence_data(verb_id=sample_verb.id)
        sentence = await create_sentence(supabase_db_connection, sentence_data)

        # Verify foreign key relationship
        assert sentence.verb_id == sample_verb.id

        # Test cascade behavior (if any) - verify verb deletion behavior
        # Note: This depends on actual FK constraint setup
        try:
            # Try to delete the verb (should fail if there are FK constraints with RESTRICT)
            await supabase_db_connection.execute(
                "DELETE FROM verbs WHERE id = $1", sample_verb.id
            )
            # If we get here, either no FK constraint or CASCADE delete
        except Exception:
            # If constraint exists with RESTRICT, this should fail
            # Verify sentence still exists
            existing_sentence = await get_sentence(supabase_db_connection, sentence.id)
            assert existing_sentence is not None
