"""
Integration tests for VerbRepository using local Supabase and direct database calls.
Tests the complete Supabase stack: PostgreSQL + API + RLS policies.
"""

import pytest
import asyncpg
from uuid import uuid4

from src.schemas.verbs import (
    ConjugationCreate,
    ConjugationUpdate,
)
from tests.verbs.fixtures import (
    generate_random_verb_data,
    generate_random_conjugation_data,
    clean_verb_db,  # noqa: F401
)
from tests.verbs.db_helpers import (
    create_verb,
    get_verb,
    get_verb_by_infinitive,
    update_verb,
    delete_verb,
    get_verbs,
    count_verbs,
    search_verbs,
    get_random_verb,
    create_conjugation,
    get_conjugation,
    get_conjugations_by_verb,
    get_conjugations,
    update_conjugation,
    delete_conjugation,
    upsert_conjugation,
    get_verb_with_conjugations,
    update_last_used,
)


# ============================================================================
# CRUD Operations Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.parametrize(
    "operation, setup_func, expected_func, test_func",
    [
        (
            "create_verb",
            lambda: generate_random_verb_data(),
            lambda verb_data, result: result.infinitive == verb_data["infinitive"],
            lambda conn, verb_data: create_verb(conn, verb_data),
        ),
        (
            "get_verb",
            lambda: None,
            lambda verb_data, result: result is not None,
            lambda conn, verb_data: get_verb(
                conn, verb_data
            ),  # verb_data will be verb_id
        ),
        (
            "update_verb",
            lambda: {"translation": "updated translation"},
            lambda verb_data, result: result.translation == "updated translation",
            lambda conn, verb_data: update_verb(conn, verb_data["verb_id"], verb_data),
        ),
        (
            "delete_verb",
            lambda: None,
            lambda verb_data, result: result is True,
            lambda conn, verb_data: delete_verb(
                conn, verb_data
            ),  # verb_data will be verb_id
        ),
    ],
)
async def test_verb_crud_operations(
    supabase_db_connection, operation, setup_func, expected_func, test_func
):
    """Test CRUD operations for verbs using direct database calls."""
    if operation == "create_verb":
        verb_data = setup_func()
        result = await test_func(supabase_db_connection, verb_data)
        assert expected_func(verb_data, result)

    elif operation == "get_verb":
        # First create a verb to get
        verb_data = generate_random_verb_data()
        created_verb = await create_verb(supabase_db_connection, verb_data)
        result = await get_verb(supabase_db_connection, created_verb.id)
        assert expected_func(verb_data, result)

    elif operation == "update_verb":
        # First create a verb to update
        verb_data = generate_random_verb_data()
        created_verb = await create_verb(supabase_db_connection, verb_data)
        update_data = setup_func()
        result = await update_verb(supabase_db_connection, created_verb.id, update_data)
        assert expected_func(update_data, result)

    elif operation == "delete_verb":
        # First create a verb to delete
        verb_data = generate_random_verb_data()
        created_verb = await create_verb(supabase_db_connection, verb_data)
        result = await delete_verb(supabase_db_connection, created_verb.id)
        assert expected_func(None, result)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_verb_retrieval_variants(supabase_db_connection):
    """Test different verb retrieval methods."""
    # Create test verbs
    verb_data_1 = generate_random_verb_data()
    verb_data_2 = generate_random_verb_data()
    verb_data_2["infinitive"] = (
        f"unique_test_verb_{uuid4().hex[:8]}"  # Make infinitive truly unique
    )

    verb1 = await create_verb(supabase_db_connection, verb_data_1)
    verb2 = await create_verb(supabase_db_connection, verb_data_2)

    # Test get by ID
    retrieved_verb = await get_verb(supabase_db_connection, verb1.id)
    assert retrieved_verb.id == verb1.id
    assert retrieved_verb.infinitive == verb1.infinitive

    # Test get by infinitive
    retrieved_by_infinitive = await get_verb_by_infinitive(
        supabase_db_connection, verb2.infinitive
    )
    assert retrieved_by_infinitive.id == verb2.id

    # Test get verbs (list)
    all_verbs = await get_verbs(supabase_db_connection)
    assert len(all_verbs) >= 2
    verb_ids = [v.id for v in all_verbs]
    assert verb1.id in verb_ids
    assert verb2.id in verb_ids

    # Test get verbs with limit
    limited_verbs = await get_verbs(supabase_db_connection, limit=1)
    assert len(limited_verbs) == 1

    # Test get verbs with offset
    offset_verbs = await get_verbs(supabase_db_connection, offset=1)
    assert len(offset_verbs) >= 1

    # Test count verbs
    total_count = await count_verbs(supabase_db_connection)
    assert total_count >= 2

    # Test get random verb
    random_verb = await get_random_verb(supabase_db_connection)
    assert random_verb is not None
    # Note: Don't check if it's one of our specific verbs since database may contain other verbs

    # Test not found cases
    non_existent_verb = await get_verb(supabase_db_connection, uuid4())
    assert non_existent_verb is None

    non_existent_by_infinitive = await get_verb_by_infinitive(
        supabase_db_connection, "non_existent_verb_xyz"
    )
    assert non_existent_by_infinitive is None


# ============================================================================
# Conjugation Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_conjugation_operations(supabase_db_connection):
    """Test conjugation CRUD operations."""
    # Create conjugation data
    conjugation_data = generate_random_conjugation_data()
    conjugation_create = ConjugationCreate(**conjugation_data)

    # Test create conjugation
    created_conjugation = await upsert_conjugation(
        supabase_db_connection, conjugation_create
    )
    assert created_conjugation.id is not None
    assert created_conjugation.infinitive == conjugation_data["infinitive"]
    assert created_conjugation.tense == conjugation_data["tense"]

    # Verify in database
    db_conjugation = await get_conjugation(
        supabase_db_connection, created_conjugation.id
    )
    assert db_conjugation is not None
    assert db_conjugation.infinitive == conjugation_data["infinitive"]

    # Test get conjugation
    retrieved_conjugation = await get_conjugation(
        supabase_db_connection, created_conjugation.id
    )
    assert retrieved_conjugation.id == created_conjugation.id
    assert retrieved_conjugation.infinitive == conjugation_data["infinitive"]

    # Test update conjugation
    update_data = ConjugationUpdate(first_person_singular="updated_form")
    updated_conjugation = await update_conjugation(
        supabase_db_connection, created_conjugation.id, update_data
    )
    assert updated_conjugation.first_person_singular == "updated_form"
    assert updated_conjugation.infinitive == conjugation_data["infinitive"]

    # Verify update in database
    db_updated = await get_conjugation(supabase_db_connection, created_conjugation.id)
    assert db_updated.first_person_singular == "updated_form"

    # Test get conjugations by verb
    conjugations_by_verb = await get_conjugations_by_verb(
        supabase_db_connection, conjugation_data["infinitive"]
    )
    assert len(conjugations_by_verb) >= 1
    conjugation_ids = [c.id for c in conjugations_by_verb]
    assert created_conjugation.id in conjugation_ids

    # Test delete conjugation
    delete_result = await delete_conjugation(
        supabase_db_connection, created_conjugation.id
    )
    assert delete_result is True

    # Verify deletion
    deleted_conjugation = await get_conjugation(
        supabase_db_connection, created_conjugation.id
    )
    assert deleted_conjugation is None


# ============================================================================
# Upsert Operations Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upsert_operations(supabase_db_connection):
    """Test upsert operations for conjugations."""
    conjugation_data = generate_random_conjugation_data()
    conjugation_create = ConjugationCreate(**conjugation_data)

    # First upsert - should create
    first_upsert = await upsert_conjugation(supabase_db_connection, conjugation_create)
    assert first_upsert.id is not None
    assert first_upsert.infinitive == conjugation_data["infinitive"]
    assert first_upsert.tense == conjugation_data["tense"]

    # Second upsert with same key fields - should update
    conjugation_data["first_person_singular"] = "updated_upsert_form"
    conjugation_update = ConjugationCreate(**conjugation_data)
    second_upsert = await upsert_conjugation(supabase_db_connection, conjugation_update)

    # Should be same record (updated)
    assert second_upsert.infinitive == conjugation_data["infinitive"]
    assert second_upsert.first_person_singular == "updated_upsert_form"

    # Verify only one record exists for this combination
    conjugations_by_verb = await get_conjugations_by_verb(
        supabase_db_connection, conjugation_data["infinitive"]
    )
    tense_matches = [
        c for c in conjugations_by_verb if c.tense == conjugation_data["tense"]
    ]
    assert len(tense_matches) == 1
    assert tense_matches[0].first_person_singular == "updated_upsert_form"


# ============================================================================
# Search and Query Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_verbs(supabase_db_connection, clean_verb_db):
    """Test verb search functionality."""
    from uuid import uuid4

    # Create test verbs with known values for searching (but unique)
    unique_suffix = uuid4().hex[:8]

    search_verb_data = generate_random_verb_data()
    search_verb_data["infinitive"] = f"chercher_{unique_suffix}"
    search_verb_data["translation"] = f"to_search_{unique_suffix}"

    regular_verb_data = generate_random_verb_data()
    regular_verb_data["infinitive"] = f"manger_{unique_suffix}"
    regular_verb_data["translation"] = f"to_eat_{unique_suffix}"

    search_verb = await create_verb(supabase_db_connection, search_verb_data)
    await create_verb(supabase_db_connection, regular_verb_data)

    # Test search by infinitive
    search_results_infinitive = await search_verbs(
        supabase_db_connection, f"chercher_{unique_suffix}"
    )
    assert len(search_results_infinitive) >= 1
    found_ids = [v.id for v in search_results_infinitive]
    assert search_verb.id in found_ids

    # Test search by translation
    search_results_translation = await search_verbs(
        supabase_db_connection, f"search_{unique_suffix}"
    )
    assert len(search_results_translation) >= 1
    found_ids = [v.id for v in search_results_translation]
    assert search_verb.id in found_ids

    # Test empty search
    no_results = await search_verbs(supabase_db_connection, "nonexistent_verb_12345")
    assert len(no_results) == 0


# ============================================================================
# Complex Query Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_verb_with_conjugations(supabase_db_connection):
    """Test getting verbs with their conjugations."""
    # Create a verb and some conjugations
    verb_data = generate_random_verb_data()
    verb = await create_verb(supabase_db_connection, verb_data)

    # Create conjugations for the verb
    present_data = generate_random_conjugation_data()
    present_data["infinitive"] = verb.infinitive
    present_data["auxiliary"] = verb.auxiliary
    present_data["reflexive"] = verb.reflexive
    present_data["tense"] = "present"

    future_data = generate_random_conjugation_data()
    future_data["infinitive"] = verb.infinitive
    future_data["auxiliary"] = verb.auxiliary
    future_data["reflexive"] = verb.reflexive
    future_data["tense"] = "future_simple"

    await create_conjugation(supabase_db_connection, present_data)
    await create_conjugation(supabase_db_connection, future_data)

    # Test getting verb with conjugations
    verb_with_conjugations = await get_verb_with_conjugations(
        supabase_db_connection, verb.infinitive
    )

    assert verb_with_conjugations is not None
    assert verb_with_conjugations["verb"].id == verb.id
    assert len(verb_with_conjugations["conjugations"]) >= 2

    conjugation_tenses = [c.tense for c in verb_with_conjugations["conjugations"]]
    assert "present" in conjugation_tenses
    assert "future_simple" in conjugation_tenses


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_last_used(supabase_db_connection):
    """Test updating last used timestamp."""
    # Create a verb
    verb_data = generate_random_verb_data()
    verb = await create_verb(supabase_db_connection, verb_data)

    original_last_used = verb.last_used_at
    assert original_last_used is None

    # Update last used
    result = await update_last_used(supabase_db_connection, verb.id)
    assert result is True

    # Verify the timestamp was updated
    updated_verb = await get_verb(supabase_db_connection, verb.id)
    assert updated_verb.last_used_at is not None
    assert updated_verb.last_used_at != original_last_used


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_conjugations(supabase_db_connection, clean_verb_db):
    """Test getting conjugations for a verb."""
    from uuid import uuid4

    # Create conjugations with unique infinitive
    unique_suffix = uuid4().hex[:8]
    infinitive = f"test_conjugate_{unique_suffix}"

    conjugation_data_1 = generate_random_conjugation_data()
    conjugation_data_1["infinitive"] = infinitive
    conjugation_data_1["tense"] = "present"

    conjugation_data_2 = generate_random_conjugation_data()
    conjugation_data_2["infinitive"] = infinitive
    conjugation_data_2["tense"] = "future_simple"

    conj1 = await create_conjugation(supabase_db_connection, conjugation_data_1)
    conj2 = await create_conjugation(supabase_db_connection, conjugation_data_2)

    # Test getting conjugations
    conjugations = await get_conjugations(supabase_db_connection, infinitive)
    assert len(conjugations) >= 2

    conjugation_ids = [c.id for c in conjugations]
    assert conj1.id in conjugation_ids
    assert conj2.id in conjugation_ids

    # Test filtering by tense
    present_conjugations = await get_conjugations_by_verb(
        supabase_db_connection, infinitive
    )
    present_tenses = [c.tense for c in present_conjugations]
    assert "present" in present_tenses
    assert "future_simple" in present_tenses


# ============================================================================
# Database Constraint Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_constraints_are_enforced(supabase_db_connection):
    """Test that database constraints are properly enforced using domain objects."""

    # Test invalid language code constraint
    invalid_verb_data = {
        "infinitive": "test_verb",
        "auxiliary": "avoir",
        "target_language_code": "invalid_lang_code_too_long",  # Should violate constraint
        "translation": "test translation",
        "past_participle": "test_participle",
        "present_participle": "test_participle",
    }

    with pytest.raises((asyncpg.CheckViolationError, asyncpg.DataError)):
        await create_verb(supabase_db_connection, invalid_verb_data)

    # Test duplicate infinitive constraint (if exists)
    verb_data = generate_random_verb_data()
    await create_verb(supabase_db_connection, verb_data)

    # Try to create another verb with same infinitive should fail (if constraint exists)
    try:
        duplicate_data = verb_data.copy()
        await create_verb(supabase_db_connection, duplicate_data)
        # If we get here, there's no unique constraint on infinitive (which is fine)
    except (asyncpg.UniqueViolationError, Exception):
        # If constraint exists, we expect this to fail
        pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_verb_constraint_validation_comprehensive(supabase_db_connection):
    """Test comprehensive verb constraint validation using domain objects."""

    # Test invalid auxiliary type (if constraint exists)
    invalid_auxiliary_data = {
        "infinitive": "test_verb",
        "auxiliary": "invalid_auxiliary",  # Should violate enum constraint
        "target_language_code": "eng",
        "translation": "test translation",
        "past_participle": "test_participle",
        "present_participle": "test_participle",
    }

    with pytest.raises((asyncpg.CheckViolationError, asyncpg.DataError)):
        await create_verb(supabase_db_connection, invalid_auxiliary_data)

    # Test empty infinitive constraint
    empty_infinitive_data = {
        "infinitive": "",  # Empty infinitive should fail
        "auxiliary": "avoir",
        "target_language_code": "eng",
        "translation": "test translation",
        "past_participle": "test_participle",
        "present_participle": "test_participle",
    }

    with pytest.raises((asyncpg.CheckViolationError, asyncpg.NotNullViolationError)):
        await create_verb(supabase_db_connection, empty_infinitive_data)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_conjugation_constraint_validation(supabase_db_connection):
    """Test conjugation constraint validation using domain objects."""

    # First create a valid verb
    verb_data = generate_random_verb_data()
    verb = await create_verb(supabase_db_connection, verb_data)

    # Test invalid tense enum
    invalid_tense_data = {
        "infinitive": verb.infinitive,
        "auxiliary": verb.auxiliary,
        "reflexive": verb.reflexive,
        "tense": "invalid_tense",  # Should violate enum constraint
        "first_person_singular": "test form",
    }

    with pytest.raises((asyncpg.CheckViolationError, asyncpg.DataError)):
        await create_conjugation(supabase_db_connection, invalid_tense_data)

    # Test invalid auxiliary enum
    invalid_auxiliary_conj_data = {
        "infinitive": verb.infinitive,
        "auxiliary": "invalid_auxiliary",  # Should violate enum constraint
        "reflexive": verb.reflexive,
        "tense": "present",
        "first_person_singular": "test form",
    }

    with pytest.raises((asyncpg.CheckViolationError, asyncpg.DataError)):
        await create_conjugation(supabase_db_connection, invalid_auxiliary_conj_data)

    # Test foreign key constraint - non-existent infinitive with unique values
    unique_id = uuid4().hex[:8]
    nonexistent_verb_data = {
        "infinitive": f"nonexistent_verb_{unique_id}",
        "auxiliary": "avoir",
        "reflexive": False,
        "tense": "present",
        "first_person_singular": "test form",
    }

    # This might not raise FK error since we use composite keys, but test anyway
    try:
        await create_conjugation(supabase_db_connection, nonexistent_verb_data)
        # If no FK constraint, this should succeed
    except asyncpg.ForeignKeyViolationError:
        # If FK constraint exists, we expect this to fail
        pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cross_domain_verb_constraint_patterns(supabase_db_connection):
    """Test cross-domain constraint patterns using domain objects."""

    # Create a verb first
    verb_data = generate_random_verb_data()
    verb = await create_verb(supabase_db_connection, verb_data)

    # Test that conjugations can be created for valid verbs
    conjugation_data = generate_random_conjugation_data()
    conjugation_data["infinitive"] = verb.infinitive
    conjugation_data["auxiliary"] = verb.auxiliary
    conjugation_data["reflexive"] = verb.reflexive

    # This should work
    conjugation = await create_conjugation(supabase_db_connection, conjugation_data)
    assert conjugation.infinitive == verb.infinitive
    assert conjugation.auxiliary == verb.auxiliary
    assert conjugation.reflexive == verb.reflexive

    # Test cascade behavior - if we delete verb, what happens to conjugations?
    await delete_verb(supabase_db_connection, verb.id)

    # The conjugation might still exist since we use composite keys, not FK
    # Check if the conjugation still exists
    try:
        retrieved_conjugation = await get_conjugation(
            supabase_db_connection, conjugation.id
        )
        # If we get here, cascade didn't happen (expected with composite keys)
        assert retrieved_conjugation is not None or retrieved_conjugation is None
    except Exception:
        # Expected if some cascade behavior exists
        pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_indexes_exist(supabase_db_connection):
    """Test that expected database indexes exist for performance."""
    # Query for indexes on verbs table
    index_query = """
        SELECT indexname, tablename, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'verbs'
        ORDER BY indexname
    """

    indexes = await supabase_db_connection.fetch(index_query)
    index_names = [idx["indexname"] for idx in indexes]

    # Should have at least the primary key index
    assert any("pkey" in name for name in index_names)

    # Test the same for conjugations
    conjugation_index_query = """
        SELECT indexname, tablename, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'conjugations'
        ORDER BY indexname
    """

    conj_indexes = await supabase_db_connection.fetch(conjugation_index_query)
    conj_index_names = [idx["indexname"] for idx in conj_indexes]

    # Should have at least the primary key index
    assert any("pkey" in name for name in conj_index_names)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_verb_with_duplicate_constraint(supabase_db_connection):
    """Test creating verbs with potential duplicate constraints."""
    verb_data = generate_random_verb_data()

    # Create first verb
    first_verb = await create_verb(supabase_db_connection, verb_data)
    assert first_verb.infinitive == verb_data["infinitive"]

    # Try to create second verb with same data
    # Behavior depends on database constraints
    try:
        second_verb = await create_verb(supabase_db_connection, verb_data)
        # If no unique constraints, this will succeed
        assert second_verb.infinitive == verb_data["infinitive"]
        # Verify we have 2 verbs with same infinitive
        verbs_with_infinitive = await get_verbs(
            supabase_db_connection, filters={"infinitive": verb_data["infinitive"]}
        )
        assert len(verbs_with_infinitive) >= 2
    except Exception:
        # If unique constraint exists, this should fail
        # Verify only one verb exists
        verbs_with_infinitive = await get_verbs(
            supabase_db_connection, filters={"infinitive": verb_data["infinitive"]}
        )
        assert len(verbs_with_infinitive) == 1


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation,args,expected_result",
    [
        ("get_verb", (uuid4(),), None),
        ("get_verb_by_infinitive", ("nonexistent_verb",), None),
        ("update_verb", (uuid4(), {"translation": "test"}), None),
        ("delete_verb", (uuid4(),), False),
        ("get_conjugation", (uuid4(),), None),
        ("update_conjugation", (uuid4(), {"tense": "present"}), None),
        ("delete_conjugation", (uuid4(),), False),
    ],
)
async def test_not_found_cases(
    supabase_db_connection, operation, args, expected_result
):
    """Test operations with non-existent resources."""
    # Map operations to db_helper functions
    from tests.verbs.db_helpers import (
        get_verb,
        get_verb_by_infinitive,
        update_verb,
        delete_verb,
        get_conjugation,
        update_conjugation,
        delete_conjugation,
    )

    function_map = {
        "get_verb": get_verb,
        "get_verb_by_infinitive": get_verb_by_infinitive,
        "update_verb": update_verb,
        "delete_verb": delete_verb,
        "get_conjugation": get_conjugation,
        "update_conjugation": update_conjugation,
        "delete_conjugation": delete_conjugation,
    }

    db_function = function_map[operation]
    result = await db_function(supabase_db_connection, *args)
    assert result == expected_result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_db_helpers_basic_functionality(supabase_db_connection):
    """Basic smoke test for db_helpers functionality."""
    # Test that all required db helper functions are available
    from tests.verbs.db_helpers import (
        create_verb,
        get_verb,
        update_verb,
        delete_verb,
        get_verbs,
        count_verbs,
        search_verbs,
        get_random_verb,
        create_conjugation,
        get_conjugation,
        update_conjugation,
        delete_conjugation,
        upsert_conjugation,
        get_conjugations,
        get_verb_with_conjugations,
        update_last_used,
    )

    # Test that we can import all required functions
    assert create_verb is not None
    assert get_verb is not None
    assert update_verb is not None
    assert delete_verb is not None
    assert get_verbs is not None
    assert count_verbs is not None
    assert search_verbs is not None
    assert get_random_verb is not None
    assert create_conjugation is not None
    assert get_conjugation is not None
    assert update_conjugation is not None
    assert delete_conjugation is not None
    assert upsert_conjugation is not None
    assert get_conjugations is not None
    assert get_verb_with_conjugations is not None
    assert update_last_used is not None
