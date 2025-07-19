"""Test cases for verb repository using Supabase client only."""

from uuid import uuid4

import pytest

from src.core.exceptions import RepositoryError
from src.repositories.verb_repository import VerbRepository
from src.schemas.verbs import (
    ConjugationCreate,
    ConjugationUpdate,
    Tense,
    VerbCreate,
    VerbUpdate,
)
from tests.verbs.fixtures import (
    generate_random_conjugation_data,
    generate_random_verb_data,
    verb_repository,  # Import the fixture
)


@pytest.mark.integration
class TestVerbRepository:
    """Test cases for VerbRepository using Supabase client operations only."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_repository_with_supabase_client(self, verb_repository):
        """Test that VerbRepository can be instantiated with Supabase client."""
        assert verb_repository.client is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_verb_failure_with_invalid_data(self, verb_repository):
        """Test that creating a verb with invalid data raises an exception."""
        # Create invalid verb data (missing required fields)
        invalid_verb_data = {"infinitive": ""}  # Empty infinitive should fail

        with pytest.raises(Exception):
            await verb_repository.create_verb(VerbCreate(**invalid_verb_data))

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_verb_db_error(self, verb_repository):
        """Test that a database constraint violation raises RepositoryError."""
        verb_data = generate_random_verb_data()
        verb_data["infinitive"] = f"unique_infinitive_{uuid4()}"
        verb_to_create = VerbCreate(**verb_data)

        # Create the verb once, which should succeed.
        await verb_repository.create_verb(verb_to_create)

        # Try to create the exact same verb again, which should fail.
        with pytest.raises(RepositoryError):
            await verb_repository.create_verb(verb_to_create)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_verb_crud_operations_create(self, verb_repository):
        """Test creating a verb using repository."""
        verb_data = generate_random_verb_data()
        verb_create = VerbCreate(**verb_data)

        result = await verb_repository.create_verb(verb_create)

        assert result.infinitive == verb_data["infinitive"]
        assert result.auxiliary == verb_data["auxiliary"]
        assert result.target_language_code == verb_data["target_language_code"]
        assert result.translation == verb_data["translation"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_verb_crud_operations_get(self, verb_repository):
        """Test getting a verb by ID using repository."""
        # First create a verb
        verb_data = generate_random_verb_data()
        created_verb = await verb_repository.create_verb(VerbCreate(**verb_data))

        # Then retrieve it
        result = await verb_repository.get_verb(created_verb.id)

        assert result is not None
        assert result.id == created_verb.id
        assert result.infinitive == verb_data["infinitive"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_verb_crud_operations_update(self, verb_repository):
        """Test updating a verb using repository."""
        # First create a verb
        verb_data = generate_random_verb_data()
        created_verb = await verb_repository.create_verb(VerbCreate(**verb_data))

        # Then update it
        update_data = VerbUpdate(translation="updated translation")
        result = await verb_repository.update_verb(created_verb.id, update_data)

        assert result is not None
        assert result.translation == "updated translation"
        assert result.infinitive == verb_data["infinitive"]  # Unchanged

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_verb_crud_operations_delete(self, verb_repository):
        """Test deleting a verb using repository."""
        # First create a verb
        verb_data = generate_random_verb_data()
        created_verb = await verb_repository.create_verb(VerbCreate(**verb_data))

        # Then delete it
        result = await verb_repository.delete_verb(created_verb.id)
        assert result is True

        # Verify it's deleted
        deleted_verb = await verb_repository.get_verb(created_verb.id)
        assert deleted_verb is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_verb_retrieval_variants(self, verb_repository):
        """Test different ways of retrieving verbs using repository."""
        # Create a unique verb for this test
        unique_suffix = uuid4().hex[:8]
        verb_data = generate_random_verb_data()
        verb_data["infinitive"] = f"test_verb_{unique_suffix}"

        created_verb = await verb_repository.create_verb(VerbCreate(**verb_data))

        # Test get by ID
        retrieved_verb = await verb_repository.get_verb(created_verb.id)
        assert retrieved_verb.id == created_verb.id

        # Test get by infinitive
        retrieved_by_infinitive = await verb_repository.get_verb_by_infinitive(
            created_verb.infinitive
        )
        assert retrieved_by_infinitive.id == created_verb.id

        # Test get all verbs - just ensure we get at least one verb (our created one)
        all_verbs = await verb_repository.get_all_verbs()
        assert len(all_verbs) >= 1  # At least our created verb should be there

        # Test get all verbs with limit
        limited_verbs = await verb_repository.get_all_verbs(limit=1)
        assert len(limited_verbs) == 1

        # Test get random verb
        random_verb = await verb_repository.get_random_verb()
        assert random_verb is not None

        # Test not found cases
        non_existent_verb = await verb_repository.get_verb(uuid4())
        assert non_existent_verb is None

        non_existent_by_infinitive = await verb_repository.get_verb_by_infinitive(
            "non_existent_verb_xyz"
        )
        assert non_existent_by_infinitive is None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_conjugation_operations(self, verb_repository):
        """Test conjugation CRUD operations using repository."""
        # Create conjugation data
        conjugation_data = generate_random_conjugation_data()
        conjugation_create = ConjugationCreate(**conjugation_data)

        # Test create conjugation
        await verb_repository.upsert_conjugation(conjugation_create)

        # Test get conjugation by verb and tense
        retrieved_conjugation = await verb_repository.get_conjugation_by_verb_and_tense(
            conjugation_data["infinitive"],
            conjugation_data["auxiliary"],
            conjugation_data["reflexive"],
            Tense(conjugation_data["tense"]),  # Convert string to Tense enum
        )
        assert retrieved_conjugation is not None
        assert retrieved_conjugation.infinitive == conjugation_data["infinitive"]
        assert retrieved_conjugation.tense == conjugation_data["tense"]

        # Test get conjugations by verb
        conjugations = await verb_repository.get_conjugations(
            conjugation_data["infinitive"],
            conjugation_data["auxiliary"],  # Add required auxiliary parameter
            conjugation_data["reflexive"],  # Add required reflexive parameter
        )
        assert len(conjugations) >= 1
        found_tenses = [c.tense for c in conjugations]
        assert conjugation_data["tense"] in found_tenses

        # Test update conjugation
        update_data = ConjugationUpdate(first_person_singular="updated_form")
        updated_conjugation = (
            await verb_repository.update_conjugation_by_verb_and_tense(
                conjugation_data["infinitive"],
                conjugation_data["auxiliary"],
                conjugation_data["reflexive"],
                Tense(conjugation_data["tense"]),  # Convert string to Tense enum
                update_data,
            )
        )
        assert updated_conjugation is not None
        assert updated_conjugation.first_person_singular == "updated_form"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_verbs(self, verb_repository):
        """Test verb search functionality using repository."""
        # Create test verbs with known values for searching
        unique_suffix = uuid4().hex[:8]

        search_verb_data = generate_random_verb_data()
        search_verb_data["infinitive"] = f"chercher_{unique_suffix}"
        search_verb_data["translation"] = f"to_search_{unique_suffix}"

        regular_verb_data = generate_random_verb_data()
        regular_verb_data["infinitive"] = f"manger_{unique_suffix}"
        regular_verb_data["translation"] = f"to_eat_{unique_suffix}"

        search_verb = await verb_repository.create_verb(VerbCreate(**search_verb_data))
        await verb_repository.create_verb(VerbCreate(**regular_verb_data))

        # Test search by infinitive
        search_results_infinitive = await verb_repository.search_verbs(
            f"chercher_{unique_suffix}"
        )
        assert len(search_results_infinitive) >= 1
        found_ids = [v.id for v in search_results_infinitive]
        assert search_verb.id in found_ids

        # Test search by translation
        search_results_translation = await verb_repository.search_verbs(
            f"search_{unique_suffix}"
        )
        assert len(search_results_translation) >= 1
        found_ids = [v.id for v in search_results_translation]
        assert search_verb.id in found_ids

        # Test empty search
        no_results = await verb_repository.search_verbs("nonexistent_verb_12345")
        assert len(no_results) == 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_verb_with_conjugations(self, verb_repository):
        """Test getting verbs with their conjugations using repository."""
        # Create a verb
        verb_data = generate_random_verb_data()
        verb = await verb_repository.create_verb(VerbCreate(**verb_data))

        # Create conjugations for the verb
        present_data = generate_random_conjugation_data()
        present_data["infinitive"] = verb.infinitive
        present_data["auxiliary"] = verb.auxiliary.value  # Convert enum to string value
        present_data["reflexive"] = verb.reflexive
        present_data["tense"] = "present"

        future_data = generate_random_conjugation_data()
        future_data["infinitive"] = verb.infinitive
        future_data["auxiliary"] = verb.auxiliary.value  # Convert enum to string value
        future_data["reflexive"] = verb.reflexive
        future_data["tense"] = "future_simple"

        await verb_repository.upsert_conjugation(ConjugationCreate(**present_data))
        await verb_repository.upsert_conjugation(ConjugationCreate(**future_data))

        # Test getting verb with conjugations
        verb_with_conjugations = await verb_repository.get_verb_with_conjugations(
            verb.infinitive,
            verb.auxiliary.value,  # Convert enum to string value
            verb.reflexive,
            verb.target_language_code,  # Include target language code to match the created verb
        )

        assert verb_with_conjugations is not None
        assert verb_with_conjugations.id == verb.id  # Access verb fields directly
        assert len(verb_with_conjugations.conjugations) >= 2

        conjugation_tenses = [c.tense for c in verb_with_conjugations.conjugations]
        assert "present" in conjugation_tenses
        assert "future_simple" in conjugation_tenses

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_last_used(self, verb_repository):
        """Test updating last used timestamp using repository."""
        # Create a verb
        verb_data = generate_random_verb_data()
        verb = await verb_repository.create_verb(VerbCreate(**verb_data))

        original_last_used = verb.last_used_at
        assert original_last_used is None

        # Update last used
        result = await verb_repository.update_last_used(verb.id)
        assert result is True

        # Verify the timestamp was updated
        updated_verb = await verb_repository.get_verb(verb.id)
        assert updated_verb.last_used_at is not None
        assert updated_verb.last_used_at != original_last_used

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "operation,args,expected_result",
        [
            ("get_verb", (uuid4(),), None),
            ("get_verb_by_infinitive", ("nonexistent_verb",), None),
            ("update_verb", (uuid4(), VerbUpdate(translation="test")), None),
            ("delete_verb", (uuid4(),), False),
        ],
    )
    async def test_not_found_cases(
        self, verb_repository, operation, args, expected_result
    ):
        """Test operations with non-existent resources using repository."""
        method = getattr(verb_repository, operation)
        result = await method(*args)
        assert result == expected_result
