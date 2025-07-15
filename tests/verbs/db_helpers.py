"""Database helpers for verb domain tests using direct asyncpg calls."""

import asyncpg
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from src.schemas.verbs import (
    Verb,
    Conjugation,
)


async def create_verb(
    connection: asyncpg.Connection, verb_data: Dict[str, Any]
) -> Verb:
    """Create a verb in the database using domain objects."""
    verb_id = uuid4()

    # Convert VerbCreate to dict if needed
    if hasattr(verb_data, "model_dump"):
        verb_data = verb_data.model_dump()

    query = """
        INSERT INTO verbs (
            id, infinitive, auxiliary, reflexive, target_language_code,
            translation, past_participle, present_participle, classification,
            is_irregular, can_have_cod, can_have_coi
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        RETURNING *
    """

    result = await connection.fetchrow(
        query,
        verb_id,
        verb_data["infinitive"],
        verb_data["auxiliary"],
        verb_data.get("reflexive", False),
        verb_data["target_language_code"],
        verb_data["translation"],
        verb_data["past_participle"],
        verb_data["present_participle"],
        verb_data.get("classification"),
        verb_data.get("is_irregular", False),
        verb_data.get("can_have_cod", True),
        verb_data.get("can_have_coi", True),
    )

    return Verb(**dict(result))


async def get_verb(connection: asyncpg.Connection, verb_id: UUID) -> Optional[Verb]:
    """Get a verb by ID."""
    query = "SELECT * FROM verbs WHERE id = $1"
    result = await connection.fetchrow(query, verb_id)

    if result:
        return Verb(**dict(result))
    return None


async def get_verb_by_infinitive(
    connection: asyncpg.Connection, infinitive: str
) -> Optional[Verb]:
    """Get a verb by infinitive."""
    query = "SELECT * FROM verbs WHERE infinitive = $1"
    result = await connection.fetchrow(query, infinitive)

    if result:
        return Verb(**dict(result))
    return None


async def update_verb(
    connection: asyncpg.Connection, verb_id: UUID, updates: Dict[str, Any]
) -> Optional[Verb]:
    """Update a verb with partial data."""
    # Convert VerbUpdate to dict if needed
    if hasattr(updates, "model_dump"):
        updates = updates.model_dump(exclude_unset=True)

    # Remove None values
    updates = {k: v for k, v in updates.items() if v is not None}

    if not updates:
        return await get_verb(connection, verb_id)

    # Build dynamic query
    set_clauses = []
    values = []
    for i, (key, value) in enumerate(updates.items(), 2):  # Start from $2
        set_clauses.append(f"{key} = ${i}")
        values.append(value)

    query = f"""
        UPDATE verbs 
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = $1
        RETURNING *
    """

    result = await connection.fetchrow(query, verb_id, *values)

    if result:
        return Verb(**dict(result))
    return None


async def delete_verb(connection: asyncpg.Connection, verb_id: UUID) -> bool:
    """Delete a verb by ID."""
    query = "DELETE FROM verbs WHERE id = $1"
    result = await connection.execute(query, verb_id)
    return result == "DELETE 1"


async def get_verbs(
    connection: asyncpg.Connection,
    offset: int = 0,
    limit: int = 50,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Verb]:
    """Get verbs with optional filtering."""
    conditions = []
    values = []

    if filters:
        for key, value in filters.items():
            if value is not None:
                conditions.append(f"{key} = ${len(values) + 1}")
                values.append(value)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT * FROM verbs 
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ${len(values) + 1} OFFSET ${len(values) + 2}
    """

    values.extend([limit, offset])
    results = await connection.fetch(query, *values)

    return [Verb(**dict(row)) for row in results]


async def count_verbs(
    connection: asyncpg.Connection, filters: Optional[Dict[str, Any]] = None
) -> int:
    """Count verbs with optional filtering."""
    conditions = []
    values = []

    if filters:
        for key, value in filters.items():
            if value is not None:
                conditions.append(f"{key} = ${len(values) + 1}")
                values.append(value)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"SELECT COUNT(*) FROM verbs {where_clause}"
    result = await connection.fetchval(query, *values)

    return result


async def search_verbs(
    connection: asyncpg.Connection, query_text: str, limit: int = 50
) -> List[Verb]:
    """Search verbs by infinitive or translation."""
    query = """
        SELECT * FROM verbs 
        WHERE infinitive ILIKE $1 OR translation ILIKE $1
        ORDER BY infinitive
        LIMIT $2
    """

    results = await connection.fetch(query, f"%{query_text}%", limit)
    return [Verb(**dict(row)) for row in results]


async def get_random_verb(connection: asyncpg.Connection) -> Optional[Verb]:
    """Get a random verb."""
    query = "SELECT * FROM verbs ORDER BY RANDOM() LIMIT 1"
    result = await connection.fetchrow(query)

    if result:
        return Verb(**dict(result))
    return None


async def update_verb_last_used(connection: asyncpg.Connection, verb_id: UUID) -> bool:
    """Update the last_used_at timestamp for a verb."""
    query = """
        UPDATE verbs 
        SET last_used_at = NOW(), updated_at = NOW()
        WHERE id = $1
    """
    result = await connection.execute(query, verb_id)
    return result == "UPDATE 1"


# Conjugation helpers


async def create_conjugation(
    connection: asyncpg.Connection, conjugation_data: Dict[str, Any]
) -> Conjugation:
    """Create a conjugation in the database using domain objects."""
    conjugation_id = uuid4()

    # Convert ConjugationCreate to dict if needed
    if hasattr(conjugation_data, "model_dump"):
        conjugation_data = conjugation_data.model_dump()

    query = """
        INSERT INTO conjugations (
            id, infinitive, auxiliary, reflexive, tense,
            first_person_singular, second_person_singular, third_person_singular,
            first_person_plural, second_person_plural, third_person_plural
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        RETURNING *
    """

    result = await connection.fetchrow(
        query,
        conjugation_id,
        conjugation_data["infinitive"],
        conjugation_data["auxiliary"],
        conjugation_data.get("reflexive", False),
        conjugation_data["tense"],
        conjugation_data.get("first_person_singular"),
        conjugation_data.get("second_person_singular"),
        conjugation_data.get("third_person_singular"),
        conjugation_data.get("first_person_plural"),
        conjugation_data.get("second_person_plural"),
        conjugation_data.get("third_person_plural"),
    )

    return Conjugation(**dict(result))


async def get_conjugation(
    connection: asyncpg.Connection, conjugation_id: UUID
) -> Optional[Conjugation]:
    """Get a conjugation by ID."""
    query = "SELECT * FROM conjugations WHERE id = $1"
    result = await connection.fetchrow(query, conjugation_id)

    if result:
        return Conjugation(**dict(result))
    return None


async def get_conjugations_by_verb(
    connection: asyncpg.Connection, infinitive: str
) -> List[Conjugation]:
    """Get all conjugations for a verb by infinitive."""
    query = "SELECT * FROM conjugations WHERE infinitive = $1 ORDER BY tense"
    results = await connection.fetch(query, infinitive)

    return [Conjugation(**dict(row)) for row in results]


async def get_conjugation_by_verb_and_tense(
    connection: asyncpg.Connection, infinitive: str, tense: str
) -> Optional[Conjugation]:
    """Get a specific conjugation by infinitive and tense."""
    query = "SELECT * FROM conjugations WHERE infinitive = $1 AND tense = $2"
    result = await connection.fetchrow(query, infinitive, tense)

    if result:
        return Conjugation(**dict(result))
    return None


async def update_conjugation(
    connection: asyncpg.Connection, conjugation_id: UUID, updates: Dict[str, Any]
) -> Optional[Conjugation]:
    """Update a conjugation with partial data."""
    # Convert ConjugationUpdate to dict if needed
    if hasattr(updates, "model_dump"):
        updates = updates.model_dump(exclude_unset=True)

    # Remove None values
    updates = {k: v for k, v in updates.items() if v is not None}

    if not updates:
        return await get_conjugation(connection, conjugation_id)

    # Build dynamic query
    set_clauses = []
    values = []
    for i, (key, value) in enumerate(updates.items(), 2):  # Start from $2
        set_clauses.append(f"{key} = ${i}")
        values.append(value)

    query = f"""
        UPDATE conjugations 
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = $1
        RETURNING *
    """

    result = await connection.fetchrow(query, conjugation_id, *values)

    if result:
        return Conjugation(**dict(result))
    return None


async def delete_conjugation(
    connection: asyncpg.Connection, conjugation_id: UUID
) -> bool:
    """Delete a conjugation by ID."""
    query = "DELETE FROM conjugations WHERE id = $1"
    result = await connection.execute(query, conjugation_id)
    return result == "DELETE 1"


async def upsert_conjugation(
    connection: asyncpg.Connection, conjugation_data: Dict[str, Any]
) -> Conjugation:
    """Insert or update a conjugation based on infinitive, auxiliary, reflexive, and tense."""
    # Convert ConjugationCreate to dict if needed
    if hasattr(conjugation_data, "model_dump"):
        conjugation_data = conjugation_data.model_dump()

    query = """
        INSERT INTO conjugations (
            id, infinitive, auxiliary, reflexive, tense,
            first_person_singular, second_person_singular, third_person_singular,
            first_person_plural, second_person_plural, third_person_plural
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        ON CONFLICT (infinitive, auxiliary, reflexive, tense)
        DO UPDATE SET
            first_person_singular = EXCLUDED.first_person_singular,
            second_person_singular = EXCLUDED.second_person_singular,
            third_person_singular = EXCLUDED.third_person_singular,
            first_person_plural = EXCLUDED.first_person_plural,
            second_person_plural = EXCLUDED.second_person_plural,
            third_person_plural = EXCLUDED.third_person_plural,
            updated_at = NOW()
        RETURNING *
    """

    result = await connection.fetchrow(
        query,
        uuid4(),
        conjugation_data["infinitive"],
        conjugation_data["auxiliary"],
        conjugation_data.get("reflexive", False),
        conjugation_data["tense"],
        conjugation_data.get("first_person_singular"),
        conjugation_data.get("second_person_singular"),
        conjugation_data.get("third_person_singular"),
        conjugation_data.get("first_person_plural"),
        conjugation_data.get("second_person_plural"),
        conjugation_data.get("third_person_plural"),
    )

    return Conjugation(**dict(result))


# Utility functions for cleaning up test data


async def clear_verbs(connection: asyncpg.Connection) -> None:
    """Clear all verbs from the database (for test cleanup)."""
    await connection.execute("DELETE FROM verbs")


async def clear_conjugations(connection: asyncpg.Connection) -> None:
    """Clear all conjugations from the database (for test cleanup)."""
    await connection.execute("DELETE FROM conjugations")


async def clear_verb_domain(connection: asyncpg.Connection) -> None:
    """Clear all verb-related data (conjugations first due to potential FK constraints)."""
    await clear_conjugations(connection)
    await clear_verbs(connection)


# Additional function aliases and complex operations needed by tests


async def update_last_used(connection: asyncpg.Connection, verb_id: UUID) -> bool:
    """Alias for update_verb_last_used to match test expectations."""
    return await update_verb_last_used(connection, verb_id)


async def get_conjugations(
    connection: asyncpg.Connection, infinitive: str
) -> List[Conjugation]:
    """Alias for get_conjugations_by_verb to match test expectations."""
    return await get_conjugations_by_verb(connection, infinitive)


async def get_verb_with_conjugations(
    connection: asyncpg.Connection, infinitive: str
) -> Optional[Dict[str, Any]]:
    """Get a verb with its conjugations in a structured format."""
    verb = await get_verb_by_infinitive(connection, infinitive)
    if not verb:
        return None

    conjugations = await get_conjugations_by_verb(connection, infinitive)

    return {"verb": verb, "conjugations": conjugations}
