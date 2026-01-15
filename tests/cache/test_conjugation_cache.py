"""Tests for ConjugationCache."""

from datetime import UTC, datetime

import pytest

from src.cache.conjugation_cache import ConjugationCache
from src.schemas.verbs import (
    AuxiliaryType,
    Conjugation,
    Tense,
    Verb,
    VerbClassification,
)


@pytest.fixture
def cache_namespace(redis_client) -> str:
    """Get the unique namespace for this test's cache keys."""
    return redis_client._test_namespace


@pytest.fixture
def sample_verbs():
    """Create sample verbs for testing."""
    now = datetime.now(UTC)
    return [
        Verb(
            id="00000000-0000-0000-0000-000000000001",
            infinitive="parler",
            auxiliary=AuxiliaryType.AVOIR,
            reflexive=False,
            target_language_code="eng",
            translation="to speak",
            past_participle="parlé",
            present_participle="parlant",
            classification=VerbClassification.FIRST_GROUP,
            is_irregular=False,
            can_have_cod=True,
            can_have_coi=True,
            created_at=now,
            updated_at=now,
        ),
    ]


@pytest.fixture
def sample_conjugations():
    """Create sample conjugations for testing."""
    now = datetime.now(UTC)
    return [
        Conjugation(
            id="00000000-0000-0000-0000-000000000101",
            infinitive="parler",
            auxiliary=AuxiliaryType.AVOIR,
            reflexive=False,
            tense=Tense.PRESENT,
            first_person_singular="je parle",
            second_person_singular="tu parles",
            third_person_singular="il parle",
            first_person_plural="nous parlons",
            second_person_plural="vous parlez",
            third_person_plural="ils parlent",
            created_at=now,
            updated_at=now,
        ),
        Conjugation(
            id="00000000-0000-0000-0000-000000000102",
            infinitive="parler",
            auxiliary=AuxiliaryType.AVOIR,
            reflexive=False,
            tense=Tense.PASSE_COMPOSE,
            first_person_singular="j'ai parlé",
            second_person_singular="tu as parlé",
            third_person_singular="il a parlé",
            first_person_plural="nous avons parlé",
            second_person_plural="vous avez parlé",
            third_person_plural="ils ont parlé",
            created_at=now,
            updated_at=now,
        ),
    ]


@pytest.fixture
def mock_repository(sample_verbs, sample_conjugations):
    """Create a mock verb repository."""

    class MockVerbRepository:
        async def get_all_verbs(self, limit=10000):
            return sample_verbs

        async def get_conjugations(self, infinitive, auxiliary, reflexive):
            return [
                c
                for c in sample_conjugations
                if c.infinitive == infinitive
                and c.auxiliary.value == auxiliary
                and c.reflexive == reflexive
            ]

        async def get_all_conjugations(self, limit=10000):
            return sample_conjugations

    return MockVerbRepository()


@pytest.mark.asyncio
class TestConjugationCache:
    """Test ConjugationCache functionality."""

    async def test_cache_initially_not_loaded(self, redis_client, cache_namespace):
        """Cache should not be loaded initially."""
        cache = ConjugationCache(redis_client, namespace=cache_namespace)
        stats = cache.get_stats()

        assert stats["loaded"] is False
        assert stats["total_conjugations"] == 0

    async def test_load_conjugations(
        self, redis_client, cache_namespace, mock_repository, sample_conjugations
    ):
        """Should load conjugations into cache."""
        cache = ConjugationCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        stats = cache.get_stats()
        assert stats["loaded"] is True
        assert stats["total_conjugations"] == len(sample_conjugations)
        assert stats["unique_verbs"] == 1

    async def test_get_conjugation_hit(self, redis_client, cache_namespace, mock_repository):
        """Should return conjugation from cache."""
        cache = ConjugationCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        conj = await cache.get_conjugation(
            infinitive="parler",
            auxiliary="avoir",
            reflexive=False,
            tense=Tense.PRESENT,
        )

        assert conj is not None
        assert conj.tense == Tense.PRESENT
        assert conj.first_person_singular == "je parle"

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0

    async def test_get_conjugation_miss(self, redis_client, cache_namespace, mock_repository):
        """Should return None for non-existent conjugation."""
        cache = ConjugationCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        conj = await cache.get_conjugation(
            infinitive="finir",
            auxiliary="avoir",
            reflexive=False,
            tense=Tense.PRESENT,
        )

        assert conj is None

        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1

    async def test_get_conjugations_for_verb(
        self, redis_client, cache_namespace, mock_repository, sample_conjugations
    ):
        """Should return all conjugations for a verb."""
        cache = ConjugationCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        conjs = await cache.get_conjugations_for_verb(
            infinitive="parler",
            auxiliary="avoir",
            reflexive=False,
        )

        assert len(conjs) == len(sample_conjugations)
        assert all(c.infinitive == "parler" for c in conjs)

    async def test_refresh_conjugation_new(self, redis_client, cache_namespace, mock_repository):
        """Should add new conjugation to cache."""
        cache = ConjugationCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        now = datetime.now(UTC)
        new_conj = Conjugation(
            id="00000000-0000-0000-0000-000000000199",
            infinitive="parler",
            auxiliary=AuxiliaryType.AVOIR,
            reflexive=False,
            tense=Tense.IMPARFAIT,
            first_person_singular="je parlais",
            second_person_singular="tu parlais",
            third_person_singular="il parlait",
            first_person_plural="nous parlions",
            second_person_plural="vous parliez",
            third_person_plural="ils parlaient",
            created_at=now,
            updated_at=now,
        )

        await cache.refresh_conjugation(new_conj)

        # Verify it's in cache
        conj = await cache.get_conjugation(
            infinitive="parler",
            auxiliary="avoir",
            reflexive=False,
            tense=Tense.IMPARFAIT,
        )
        assert conj is not None
        assert conj.first_person_singular == "je parlais"

    async def test_refresh_conjugation_update(self, redis_client, cache_namespace, mock_repository):
        """Should update existing conjugation in cache."""
        cache = ConjugationCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        now = datetime.now(UTC)
        updated_conj = Conjugation(
            id="00000000-0000-0000-0000-000000000101",
            infinitive="parler",
            auxiliary=AuxiliaryType.AVOIR,
            reflexive=False,
            tense=Tense.PRESENT,
            first_person_singular="je parle bien",  # Modified
            second_person_singular="tu parles",
            third_person_singular="il parle",
            first_person_plural="nous parlons",
            second_person_plural="vous parlez",
            third_person_plural="ils parlent",
            created_at=now,
            updated_at=now,
        )

        await cache.refresh_conjugation(updated_conj)

        # Verify it's updated
        conj = await cache.get_conjugation(
            infinitive="parler",
            auxiliary="avoir",
            reflexive=False,
            tense=Tense.PRESENT,
        )
        assert conj.first_person_singular == "je parle bien"

    async def test_invalidate_verb_conjugations(self, redis_client, cache_namespace, mock_repository):
        """Should remove all conjugations for a verb."""
        cache = ConjugationCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        # Verify conjugations exist
        conjs = await cache.get_conjugations_for_verb(
            infinitive="parler",
            auxiliary="avoir",
            reflexive=False,
        )
        assert len(conjs) == 2

        # Invalidate
        await cache.invalidate_verb_conjugations(
            infinitive="parler",
            auxiliary="avoir",
            reflexive=False,
        )

        # Verify they're gone
        conjs = await cache.get_conjugations_for_verb(
            infinitive="parler",
            auxiliary="avoir",
            reflexive=False,
        )
        assert len(conjs) == 0

    async def test_hit_rate_calculation(self, redis_client, cache_namespace, mock_repository):
        """Should calculate hit rate correctly."""
        cache = ConjugationCache(redis_client, namespace=cache_namespace)
        await cache.load(mock_repository)

        # Generate hits and misses
        await cache.get_conjugation("parler", "avoir", False, Tense.PRESENT)  # hit
        await cache.get_conjugation("parler", "avoir", False, Tense.PRESENT)  # hit
        await cache.get_conjugation("finir", "avoir", False, Tense.PRESENT)  # miss

        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == "66.67%"
