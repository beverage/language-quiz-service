"""Tests for VerbCache."""

from datetime import UTC, datetime, timezone

import pytest

from src.cache.verb_cache import VerbCache
from src.schemas.verbs import AuxiliaryType, Verb, VerbClassification


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
        Verb(
            id="00000000-0000-0000-0000-000000000002",
            infinitive="être",
            auxiliary=AuxiliaryType.ETRE,
            reflexive=False,
            target_language_code="eng",
            translation="to be",
            past_participle="été",
            present_participle="étant",
            classification=VerbClassification.THIRD_GROUP,
            is_irregular=True,
            can_have_cod=False,
            can_have_coi=False,
            created_at=now,
            updated_at=now,
        ),
        Verb(
            id="00000000-0000-0000-0000-000000000003",
            infinitive="se laver",
            auxiliary=AuxiliaryType.ETRE,
            reflexive=True,
            target_language_code="eng",
            translation="to wash oneself",
            past_participle="lavé",
            present_participle="lavant",
            classification=VerbClassification.FIRST_GROUP,
            is_irregular=False,
            can_have_cod=False,
            can_have_coi=False,
            created_at=now,
            updated_at=now,
        ),
    ]


@pytest.fixture
def mock_repository(sample_verbs):
    """Create a mock verb repository."""

    class MockVerbRepository:
        async def get_all_verbs(self, limit=10000):
            return sample_verbs

    return MockVerbRepository()


@pytest.mark.asyncio
class TestVerbCache:
    """Test VerbCache functionality."""

    async def test_cache_initially_not_loaded(self):
        """Cache should not be loaded initially."""
        cache = VerbCache()
        stats = cache.get_stats()

        assert stats["loaded"] is False
        assert stats["total_verbs"] == 0

    async def test_load_verbs(self, mock_repository, sample_verbs):
        """Should load verbs into cache."""
        cache = VerbCache()
        await cache.load(mock_repository)

        stats = cache.get_stats()
        assert stats["loaded"] is True
        assert stats["total_verbs"] == len(sample_verbs)
        assert stats["languages"] == 1

    async def test_get_by_id_hit(self, mock_repository, sample_verbs):
        """Should return verb from cache by ID."""
        cache = VerbCache()
        await cache.load(mock_repository)

        verb = await cache.get_by_id(sample_verbs[0].id)
        assert verb is not None
        assert verb.infinitive == "parler"

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0

    async def test_get_by_id_miss(self, mock_repository):
        """Should return None for non-existent verb ID."""
        cache = VerbCache()
        await cache.load(mock_repository)

        verb = await cache.get_by_id("99999999-9999-9999-9999-999999999999")
        assert verb is None

        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1

    async def test_get_by_infinitive_hit(self, mock_repository):
        """Should return verb from cache by infinitive and parameters."""
        cache = VerbCache()
        await cache.load(mock_repository)

        verb = await cache.get_by_infinitive(
            infinitive="parler",
            auxiliary="avoir",
            reflexive=False,
            target_language_code="eng",
        )

        assert verb is not None
        assert verb.infinitive == "parler"
        assert verb.auxiliary == AuxiliaryType.AVOIR

    async def test_get_by_infinitive_reflexive_distinction(self, mock_repository):
        """Should distinguish between reflexive and non-reflexive verbs."""
        cache = VerbCache()
        await cache.load(mock_repository)

        # Non-reflexive
        verb1 = await cache.get_by_infinitive(
            infinitive="se laver",
            auxiliary="être",
            reflexive=False,
            target_language_code="eng",
        )
        assert verb1 is None

        # Reflexive
        verb2 = await cache.get_by_infinitive(
            infinitive="se laver",
            auxiliary="être",
            reflexive=True,
            target_language_code="eng",
        )
        assert verb2 is not None
        assert verb2.reflexive is True

    async def test_get_all_by_language(self, mock_repository, sample_verbs):
        """Should return all verbs for a language."""
        cache = VerbCache()
        await cache.load(mock_repository)

        verbs = await cache.get_all_by_language("eng")
        assert len(verbs) == len(sample_verbs)

    async def test_refresh_verb_new(self, mock_repository, sample_verbs):
        """Should add new verb to cache."""
        from datetime import datetime, timezone

        cache = VerbCache()
        await cache.load(mock_repository)

        now = datetime.now(UTC)
        new_verb = Verb(
            id="00000000-0000-0000-0000-000000000099",
            infinitive="finir",
            auxiliary=AuxiliaryType.AVOIR,
            reflexive=False,
            target_language_code="eng",
            translation="to finish",
            past_participle="fini",
            present_participle="finissant",
            classification=VerbClassification.SECOND_GROUP,
            is_irregular=False,
            can_have_cod=True,
            can_have_coi=True,
            created_at=now,
            updated_at=now,
        )

        await cache.refresh_verb(new_verb)

        # Verify it's in cache
        verb = await cache.get_by_id(new_verb.id)
        assert verb is not None
        assert verb.infinitive == "finir"

    async def test_refresh_verb_update(self, mock_repository, sample_verbs):
        """Should update existing verb in cache."""
        from datetime import datetime, timezone

        cache = VerbCache()
        await cache.load(mock_repository)

        # Update the verb
        now = datetime.now(UTC)
        updated_verb = Verb(
            id=sample_verbs[0].id,
            infinitive="parler",
            auxiliary=AuxiliaryType.AVOIR,
            reflexive=False,
            target_language_code="eng",
            translation="to speak fluently",  # Changed translation
            past_participle="parlé",
            present_participle="parlant",
            classification=VerbClassification.FIRST_GROUP,
            is_irregular=False,
            can_have_cod=True,
            can_have_coi=True,
            created_at=now,
            updated_at=now,
        )

        await cache.refresh_verb(updated_verb)

        # Verify it's updated
        verb = await cache.get_by_id(sample_verbs[0].id)
        assert verb.translation == "to speak fluently"

    async def test_invalidate_verb(self, mock_repository, sample_verbs):
        """Should remove verb from cache."""
        cache = VerbCache()
        await cache.load(mock_repository)

        # Verify verb exists
        verb = await cache.get_by_id(sample_verbs[0].id)
        assert verb is not None

        # Invalidate
        await cache.invalidate_verb(sample_verbs[0].id)

        # Verify it's gone
        verb = await cache.get_by_id(sample_verbs[0].id)
        assert verb is None

    async def test_hit_rate_calculation(self, mock_repository, sample_verbs):
        """Should calculate hit rate correctly."""
        from uuid import UUID

        cache = VerbCache()
        await cache.load(mock_repository)

        # Generate some hits and misses (must use UUID objects, not strings)
        verb_id = UUID("00000000-0000-0000-0000-000000000001")
        missing_id = UUID("99999999-9999-9999-9999-999999999999")

        await cache.get_by_id(verb_id)  # hit
        await cache.get_by_id(verb_id)  # hit
        await cache.get_by_id(verb_id)  # hit
        await cache.get_by_id(missing_id)  # miss

        stats = cache.get_stats()
        assert stats["hits"] == 3
        assert stats["misses"] == 1
        assert stats["hit_rate"] == "75.00%"

    async def test_cache_returns_copy(self, mock_repository, sample_verbs):
        """Should return a copy of list to prevent external modification."""
        cache = VerbCache()
        await cache.load(mock_repository)

        verbs1 = await cache.get_all_by_language("eng")
        verbs2 = await cache.get_all_by_language("eng")

        # Modify one list
        verbs1.append(None)

        # Other list should be unaffected
        assert len(verbs2) == len(sample_verbs)

    async def test_cache_miss_before_loaded(self):
        """Should return None and increment misses if cache not loaded."""
        cache = VerbCache()

        verb = await cache.get_by_id("00000000-0000-0000-0000-000000000001")
        assert verb is None

        stats = cache.get_stats()
        assert stats["misses"] == 1
        assert stats["loaded"] is False
