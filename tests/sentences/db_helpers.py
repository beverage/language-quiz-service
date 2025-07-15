"""Database helpers for sentence domain tests using direct asyncpg calls."""

import asyncpg
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from src.schemas.sentences import (
    Sentence,
)


async def create_sentence(
    connection: asyncpg.Connection, sentence_data: Dict[str, Any]
) -> Sentence:
    """Create a sentence in the database using domain objects."""
    sentence_id = uuid4()

    # Convert SentenceCreate to dict if needed
    if hasattr(sentence_data, "model_dump"):
        sentence_data = sentence_data.model_dump()

    query = """
        INSERT INTO sentences (
            id, target_language_code, content, translation, verb_id,
            pronoun, tense, direct_object, indirect_object, negation,
            is_correct, explanation, source
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        RETURNING *
    """

    result = await connection.fetchrow(
        query,
        sentence_id,
        sentence_data.get("target_language_code", "eng"),
        sentence_data["content"],
        sentence_data["translation"],
        sentence_data["verb_id"],
        sentence_data["pronoun"],
        sentence_data["tense"],
        sentence_data["direct_object"],
        sentence_data["indirect_object"],
        sentence_data["negation"],
        sentence_data.get("is_correct", True),
        sentence_data.get("explanation"),
        sentence_data.get("source"),
    )

    return Sentence(**dict(result))


async def get_sentence(
    connection: asyncpg.Connection, sentence_id: UUID
) -> Optional[Sentence]:
    """Get a sentence by ID."""
    query = "SELECT * FROM sentences WHERE id = $1"
    result = await connection.fetchrow(query, sentence_id)

    if result:
        return Sentence(**dict(result))
    return None


async def update_sentence(
    connection: asyncpg.Connection, sentence_id: UUID, updates: Dict[str, Any]
) -> Optional[Sentence]:
    """Update a sentence with partial data."""
    # Convert SentenceUpdate to dict if needed
    if hasattr(updates, "model_dump"):
        updates = updates.model_dump(exclude_unset=True)

    # Remove None values
    updates = {k: v for k, v in updates.items() if v is not None}

    if not updates:
        return await get_sentence(connection, sentence_id)

    # Build dynamic query
    set_clauses = []
    values = []
    for i, (key, value) in enumerate(updates.items(), 2):  # Start from $2
        set_clauses.append(f"{key} = ${i}")
        values.append(value)

    query = f"""
        UPDATE sentences 
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = $1
        RETURNING *
    """

    result = await connection.fetchrow(query, sentence_id, *values)

    if result:
        return Sentence(**dict(result))
    return None


async def delete_sentence(connection: asyncpg.Connection, sentence_id: UUID) -> bool:
    """Delete a sentence by ID."""
    query = "DELETE FROM sentences WHERE id = $1"
    result = await connection.execute(query, sentence_id)
    return result == "DELETE 1"


async def get_sentences(
    connection: asyncpg.Connection,
    offset: int = 0,
    limit: int = 50,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Sentence]:
    """Get sentences with optional filtering."""
    conditions = []
    values = []

    if filters:
        for key, value in filters.items():
            if value is not None:
                if key == "verb_ids" and isinstance(value, list):
                    # Handle list of verb IDs with ANY
                    conditions.append(f"verb_id = ANY(${len(values) + 1})")
                    values.append(value)
                else:
                    conditions.append(f"{key} = ${len(values) + 1}")
                    values.append(value)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT * FROM sentences 
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ${len(values) + 1} OFFSET ${len(values) + 2}
    """

    values.extend([limit, offset])
    results = await connection.fetch(query, *values)

    return [Sentence(**dict(row)) for row in results]


async def count_sentences(
    connection: asyncpg.Connection, filters: Optional[Dict[str, Any]] = None
) -> int:
    """Count sentences with optional filtering."""
    conditions = []
    values = []

    if filters:
        for key, value in filters.items():
            if value is not None:
                if key == "verb_ids" and isinstance(value, list):
                    # Handle list of verb IDs with ANY
                    conditions.append(f"verb_id = ANY(${len(values) + 1})")
                    values.append(value)
                else:
                    conditions.append(f"{key} = ${len(values) + 1}")
                    values.append(value)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"SELECT COUNT(*) FROM sentences {where_clause}"
    result = await connection.fetchval(query, *values)

    return result


async def get_sentences_by_verb(
    connection: asyncpg.Connection, verb_id: UUID, limit: int = 50
) -> List[Sentence]:
    """Get sentences for a specific verb."""
    query = """
        SELECT * FROM sentences 
        WHERE verb_id = $1
        ORDER BY created_at DESC
        LIMIT $2
    """

    results = await connection.fetch(query, verb_id, limit)
    return [Sentence(**dict(row)) for row in results]


async def get_random_sentence(
    connection: asyncpg.Connection, filters: Optional[Dict[str, Any]] = None
) -> Optional[Sentence]:
    """Get a random sentence with optional filtering."""
    conditions = []
    values = []

    if filters:
        for key, value in filters.items():
            if value is not None:
                if key == "verb_ids" and isinstance(value, list):
                    # Handle list of verb IDs with ANY
                    conditions.append(f"verb_id = ANY(${len(values) + 1})")
                    values.append(value)
                else:
                    conditions.append(f"{key} = ${len(values) + 1}")
                    values.append(value)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"SELECT * FROM sentences {where_clause} ORDER BY RANDOM() LIMIT 1"
    result = await connection.fetchrow(query, *values)

    if result:
        return Sentence(**dict(result))
    return None


async def get_sentences_by_content(
    connection: asyncpg.Connection, content: str
) -> List[Sentence]:
    """Get sentences by content (exact match)."""
    query = "SELECT * FROM sentences WHERE content = $1"
    results = await connection.fetch(query, content)

    return [Sentence(**dict(row)) for row in results]


async def search_sentences(
    connection: asyncpg.Connection, query_text: str, limit: int = 50
) -> List[Sentence]:
    """Search sentences by content or translation."""
    query = """
        SELECT * FROM sentences 
        WHERE content ILIKE $1 OR translation ILIKE $1
        ORDER BY created_at DESC
        LIMIT $2
    """

    results = await connection.fetch(query, f"%{query_text}%", limit)
    return [Sentence(**dict(row)) for row in results]


async def get_sentences_with_complex_filters(
    connection: asyncpg.Connection,
    pronoun: Optional[str] = None,
    tense: Optional[str] = None,
    direct_object: Optional[str] = None,
    indirect_object: Optional[str] = None,
    negation: Optional[str] = None,
    is_correct: Optional[bool] = None,
    target_language_code: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Sentence]:
    """Get sentences with complex filtering options."""
    conditions = []
    values = []

    filter_map = {
        "pronoun": pronoun,
        "tense": tense,
        "direct_object": direct_object,
        "indirect_object": indirect_object,
        "negation": negation,
        "is_correct": is_correct,
        "target_language_code": target_language_code,
    }

    for key, value in filter_map.items():
        if value is not None:
            conditions.append(f"{key} = ${len(values) + 1}")
            values.append(value)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT * FROM sentences 
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ${len(values) + 1} OFFSET ${len(values) + 2}
    """

    values.extend([limit, offset])
    results = await connection.fetch(query, *values)

    return [Sentence(**dict(row)) for row in results]


# Utility functions for cleaning up test data


async def clear_sentences(connection: asyncpg.Connection) -> None:
    """Clear all sentences from the database (for test cleanup)."""
    await connection.execute("DELETE FROM sentences")


# Specific test utility functions


async def create_sentence_with_verb(
    connection: asyncpg.Connection,
    verb_id: UUID,
    content: str = "Je parle français.",
    translation: str = "I speak French.",
    pronoun: str = "first_person",
    tense: str = "present",
    direct_object: str = "none",
    indirect_object: str = "none",
    negation: str = "none",
    is_correct: bool = True,
    explanation: Optional[str] = None,
    source: Optional[str] = None,
    target_language_code: str = "eng",
) -> Sentence:
    """Create a sentence with a specific verb ID for testing."""
    sentence_data = {
        "target_language_code": target_language_code,
        "content": content,
        "translation": translation,
        "verb_id": verb_id,
        "pronoun": pronoun,
        "tense": tense,
        "direct_object": direct_object,
        "indirect_object": indirect_object,
        "negation": negation,
        "is_correct": is_correct,
        "explanation": explanation,
        "source": source,
    }

    return await create_sentence(connection, sentence_data)


async def create_test_sentences_batch(
    connection: asyncpg.Connection, verb_id: UUID, count: int = 3
) -> List[Sentence]:
    """Create multiple test sentences for a verb."""
    sentences = []

    test_data = [
        {
            "content": "Je parle français.",
            "translation": "I speak French.",
            "pronoun": "first_person",
            "tense": "present",
        },
        {
            "content": "Tu parles anglais.",
            "translation": "You speak English.",
            "pronoun": "second_person",
            "tense": "present",
        },
        {
            "content": "Il a parlé hier.",
            "translation": "He spoke yesterday.",
            "pronoun": "third_person",
            "tense": "passe_compose",
        },
    ]

    for i in range(min(count, len(test_data))):
        data = test_data[i]
        sentence = await create_sentence_with_verb(
            connection,
            verb_id,
            content=data["content"],
            translation=data["translation"],
            pronoun=data["pronoun"],
            tense=data["tense"],
        )
        sentences.append(sentence)

    return sentences
