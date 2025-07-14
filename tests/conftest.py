# tests/conftest.py
"""Shared fixtures for the test suite."""

import pytest

from datetime import datetime, timezone
from uuid import uuid4

from src.schemas.verbs import (
    AuxiliaryType,
    VerbClassification,
    VerbCreate,
    Verb,
    ConjugationCreate,
    Conjugation,
    Tense,
)
from src.schemas.problems import ProblemType
from src.schemas.sentences import (
    SentenceCreate,
    Sentence,
    Pronoun,
    DirectObject,
    IndirectObject,
    Negation,
)

from unittest.mock import MagicMock, AsyncMock


# Environment variables are now handled via default values in Settings class


@pytest.fixture
def sample_verb_data() -> dict:
    """Provides a dictionary of valid verb data for testing."""
    return {
        "infinitive": "parler",
        "auxiliary": AuxiliaryType.AVOIR,
        "reflexive": False,
        "target_language_code": "eng",
        "translation": "to speak",
        "past_participle": "parlé",
        "present_participle": "parlant",
        "classification": VerbClassification.FIRST_GROUP,
        "is_irregular": False,
    }


@pytest.fixture
def sample_irregular_verb_data() -> dict:
    """Provides a dictionary of valid irregular verb data for testing."""
    return {
        "infinitive": "être",
        "auxiliary": AuxiliaryType.ETRE,
        "reflexive": False,
        "target_language_code": "eng",
        "translation": "to be",
        "past_participle": "été",
        "present_participle": "étant",
        "classification": VerbClassification.THIRD_GROUP,
        "is_irregular": True,
    }


@pytest.fixture
def sample_verb_create(sample_verb_data: dict) -> VerbCreate:
    """Provides a valid VerbCreate instance for testing."""
    return VerbCreate(**sample_verb_data)


@pytest.fixture
def sample_irregular_verb(sample_irregular_verb_data: dict) -> VerbCreate:
    """Provides a valid irregular VerbCreate instance for testing."""
    return VerbCreate(**sample_irregular_verb_data)


@pytest.fixture
def sample_db_verb(sample_verb_data: dict) -> Verb:
    """Provides a valid Verb instance as if it were from the database."""
    return Verb(
        id=uuid4(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        **sample_verb_data,
    )


@pytest.fixture
def sample_conjugation_create(sample_db_verb: Verb) -> ConjugationCreate:
    """Provides a valid ConjugationCreate instance for testing."""
    return ConjugationCreate(
        infinitive=sample_db_verb.infinitive,
        auxiliary=sample_db_verb.auxiliary,
        reflexive=sample_db_verb.reflexive,
        tense=Tense.PRESENT,
        first_person_singular="parle",
        second_person_singular="parles",
        third_person_singular="parle",
        first_person_plural="parlons",
        second_person_formal="parlez",
        third_person_plural="parlent",
    )


@pytest.fixture
def sample_db_conjugation(sample_conjugation_create: ConjugationCreate) -> Conjugation:
    """Provides a valid Conjugation instance as if from the database."""
    return Conjugation(
        id=uuid4(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        **sample_conjugation_create.model_dump(),
    )


@pytest.fixture
def sample_sentence_data(sample_db_verb: Verb) -> dict:
    """Provides a dictionary of valid sentence data for testing."""
    return {
        "target_language_code": "eng",
        "content": "Je parle.",
        "translation": "I am speaking.",
        "verb_id": sample_db_verb.id,
        "pronoun": Pronoun.FIRST_PERSON,
        "tense": Tense.PRESENT,
        "direct_object": DirectObject.NONE,
        "indirect_object": IndirectObject.NONE,
        "negation": Negation.NONE,
        "is_correct": True,
    }


@pytest.fixture
def sample_sentence(sample_sentence_data: dict) -> SentenceCreate:
    """Provides a valid SentenceCreate instance for testing."""
    return SentenceCreate(**sample_sentence_data)


@pytest.fixture
def sample_db_sentence(sample_sentence_data: dict) -> Sentence:
    """Provides a valid Sentence instance as if from the database."""
    return Sentence(
        id=uuid4(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        **sample_sentence_data,
    )


class SupabaseMockBuilder:
    """Builder for creating Supabase client mocks with fluent interface."""

    def __init__(self):
        self.mock_client = MagicMock()
        self._table_mock = MagicMock()
        self.mock_client.table.return_value = self._table_mock

    def with_select_response(self, data, count=None):
        """Configure a select operation response."""
        mock_response = MagicMock()
        mock_response.data = data
        if count is not None:
            mock_response.count = count

        # Create a fresh chain mock for select operations
        select_chain = MagicMock()
        select_chain.eq.return_value = select_chain
        select_chain.limit.return_value = select_chain
        select_chain.range.return_value = select_chain
        select_chain.order.return_value = select_chain
        select_chain.gte.return_value = select_chain
        select_chain.lte.return_value = select_chain
        select_chain.contains.return_value = select_chain
        select_chain.or_.return_value = select_chain
        select_chain.execute = AsyncMock(return_value=mock_response)

        self._table_mock.select.return_value = select_chain
        return self

    def with_insert_response(self, data):
        """Configure an insert operation response."""
        mock_response = MagicMock()
        mock_response.data = data

        insert_chain = MagicMock()
        insert_chain.execute = AsyncMock(return_value=mock_response)

        self._table_mock.insert.return_value = insert_chain
        return self

    def with_update_response(self, data):
        """Configure an update operation response."""
        mock_response = MagicMock()
        mock_response.data = data

        update_chain = MagicMock()
        update_chain.eq.return_value = update_chain
        update_chain.execute = AsyncMock(return_value=mock_response)

        self._table_mock.update.return_value = update_chain
        return self

    def with_delete_response(self, data):
        """Configure a delete operation response."""
        mock_response = MagicMock()
        mock_response.data = data

        delete_chain = MagicMock()
        delete_chain.eq.return_value = delete_chain
        delete_chain.execute = AsyncMock(return_value=mock_response)

        self._table_mock.delete.return_value = delete_chain
        return self

    def build(self):
        """Return the configured mock client."""
        return self.mock_client


@pytest.fixture
def supabase_mock_builder():
    """Provides a builder for creating fresh Supabase mocks."""
    return SupabaseMockBuilder


@pytest.fixture
def sample_problem_data():
    """Sample problem data for testing."""
    from datetime import datetime, timezone
    from uuid import uuid4

    return {
        "id": uuid4(),
        "problem_type": ProblemType.GRAMMAR,
        "title": "Article Agreement",
        "instructions": "Choose the correct sentence",
        "correct_answer_index": 0,
        "target_language_code": "eng",
        "statements": [
            {
                "content": "Je mange une pomme.",
                "is_correct": True,
                "translation": "I eat an apple.",
            },
            {
                "content": "Je mange un pomme.",
                "is_correct": False,
                "explanation": "Wrong article",
            },
        ],
        "topic_tags": ["grammar", "articles"],
        "source_statement_ids": [uuid4(), uuid4()],
        "metadata": {"difficulty": "intermediate"},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_problem_create_data():
    """Sample problem create data for testing."""
    from uuid import uuid4

    return {
        "problem_type": ProblemType.GRAMMAR,
        "title": "Article Agreement",
        "instructions": "Choose the correct sentence",
        "correct_answer_index": 0,
        "target_language_code": "eng",
        "statements": [
            {
                "content": "Je mange une pomme.",
                "is_correct": True,
                "translation": "I eat an apple.",
            },
            {
                "content": "Je mange un pomme.",
                "is_correct": False,
                "explanation": "Wrong article",
            },
        ],
        "topic_tags": ["grammar", "articles"],
        "source_statement_ids": [uuid4(), uuid4()],
        "metadata": {"difficulty": "intermediate"},
    }


@pytest.fixture
def sample_problem(sample_problem_data):
    """Sample Problem instance for testing."""
    from src.schemas.problems import Problem

    return Problem(**sample_problem_data)


@pytest.fixture
def sample_problem_create(sample_problem_create_data):
    """Sample ProblemCreate instance for testing."""
    from src.schemas.problems import ProblemCreate

    return ProblemCreate(**sample_problem_create_data)
