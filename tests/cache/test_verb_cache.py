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

    async def test_get_random_verb_hit(self, mock_repository, sample_verbs):
        """Should return a random verb from cache."""
        cache = VerbCache()
        await cache.load(mock_repository)

        verb = await cache.get_random_verb("eng")
        assert verb is not None
        assert verb.target_language_code == "eng"
        assert verb.infinitive in [v.infinitive for v in sample_verbs]

        stats = cache.get_stats()
        assert stats["hits"] == 1

    async def test_get_random_verb_miss_not_loaded(self):
        """Should return None if cache not loaded."""
        cache = VerbCache()

        verb = await cache.get_random_verb("eng")
        assert verb is None

        stats = cache.get_stats()
        assert stats["misses"] == 1
        assert stats["loaded"] is False

    async def test_get_random_verb_miss_no_language(self, mock_repository):
        """Should return None if no verbs for specified language."""
        cache = VerbCache()
        await cache.load(mock_repository)

        verb = await cache.get_random_verb("deu")  # German - not in sample data
        assert verb is None

        stats = cache.get_stats()
        assert stats["misses"] == 1

    async def test_get_random_verb_distribution(self, mock_repository, sample_verbs):
        """Should randomly select from available verbs."""
        cache = VerbCache()
        await cache.load(mock_repository)

        # Get multiple random verbs
        selected_verbs = set()
        for _ in range(20):
            verb = await cache.get_random_verb("eng")
            if verb:
                selected_verbs.add(verb.infinitive)

        # Should have gotten different verbs (with high probability)
        # With 3 verbs and 20 selections, we should see at least 2 different ones
        assert len(selected_verbs) >= 2

    async def test_get_random_verb_requires_cod_filters_verbs(self, mock_repository):
        """Should only return verbs with can_have_cod=True when requires_cod=True."""
        cache = VerbCache()
        await cache.load(mock_repository)

        # Get random verb with COD requirement multiple times
        for _ in range(10):
            verb = await cache.get_random_verb("eng", requires_cod=True)
            assert verb is not None
            assert verb.can_have_cod is True
            # "parler" is the only verb in sample_verbs with can_have_cod=True
            assert verb.infinitive == "parler"

    async def test_get_random_verb_requires_coi_filters_verbs(self, mock_repository):
        """Should only return verbs with can_have_coi=True when requires_coi=True."""
        cache = VerbCache()
        await cache.load(mock_repository)

        # Get random verb with COI requirement multiple times
        for _ in range(10):
            verb = await cache.get_random_verb("eng", requires_coi=True)
            assert verb is not None
            assert verb.can_have_coi is True
            # "parler" is the only verb in sample_verbs with can_have_coi=True
            assert verb.infinitive == "parler"

    async def test_get_random_verb_requires_both_cod_and_coi(self, mock_repository):
        """Should only return verbs with both can_have_cod and can_have_coi when both required."""
        cache = VerbCache()
        await cache.load(mock_repository)

        # Get random verb with both requirements
        for _ in range(10):
            verb = await cache.get_random_verb(
                "eng", requires_cod=True, requires_coi=True
            )
            assert verb is not None
            assert verb.can_have_cod is True
            assert verb.can_have_coi is True
            assert verb.infinitive == "parler"

    async def test_get_random_verb_no_matching_cod_verbs_returns_none(self):
        """Should return None if no verbs match COD requirement."""
        now = datetime.now(UTC)
        # Create verbs that all have can_have_cod=False
        verbs_without_cod = [
            Verb(
                id="00000000-0000-0000-0000-000000000001",
                infinitive="aller",
                auxiliary=AuxiliaryType.ETRE,
                reflexive=False,
                target_language_code="eng",
                translation="to go",
                past_participle="allé",
                present_participle="allant",
                classification=VerbClassification.THIRD_GROUP,
                is_irregular=True,
                can_have_cod=False,
                can_have_coi=False,
                created_at=now,
                updated_at=now,
            ),
        ]

        class MockRepo:
            async def get_all_verbs(self, limit=10000):
                return verbs_without_cod

        cache = VerbCache()
        await cache.load(MockRepo())

        verb = await cache.get_random_verb("eng", requires_cod=True)
        assert verb is None

    async def test_get_random_verb_no_matching_coi_verbs_returns_none(self):
        """Should return None if no verbs match COI requirement."""
        now = datetime.now(UTC)
        # Create verbs that all have can_have_coi=False
        verbs_without_coi = [
            Verb(
                id="00000000-0000-0000-0000-000000000001",
                infinitive="dormir",
                auxiliary=AuxiliaryType.AVOIR,
                reflexive=False,
                target_language_code="eng",
                translation="to sleep",
                past_participle="dormi",
                present_participle="dormant",
                classification=VerbClassification.THIRD_GROUP,
                is_irregular=False,
                can_have_cod=False,
                can_have_coi=False,
                created_at=now,
                updated_at=now,
            ),
        ]

        class MockRepo:
            async def get_all_verbs(self, limit=10000):
                return verbs_without_coi

        cache = VerbCache()
        await cache.load(MockRepo())

        verb = await cache.get_random_verb("eng", requires_coi=True)
        assert verb is None
