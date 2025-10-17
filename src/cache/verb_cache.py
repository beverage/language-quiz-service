"""In-memory cache for verbs with multiple access patterns."""

import asyncio
import logging
from uuid import UUID

from opentelemetry import trace

from src.schemas.verbs import Verb

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class VerbCache:
    """
    In-memory cache for verbs with multiple indexes for different access patterns.

    Thread-safe using asyncio.Lock for concurrent access.
    """

    def __init__(self):
        # Primary index: by UUID
        self._verbs_by_id: dict[UUID, Verb] = {}

        # Secondary index: by (infinitive, auxiliary, reflexive, target_language_code)
        self._verbs_by_key: dict[tuple[str, str, bool, str], Verb] = {}

        # Index for random selection: by target_language_code
        self._verbs_by_language: dict[str, list[Verb]] = {}

        self._loaded = False
        self._lock = asyncio.Lock()

        # Metrics
        self._hits = 0
        self._misses = 0

    async def load(self, repository):
        """Load all verbs into cache at startup."""
        with tracer.start_as_current_span("verb_cache.load"):
            async with self._lock:
                # Duck typing: check for the method we need instead of isinstance
                if not hasattr(repository, "get_all_verbs"):
                    raise TypeError("Repository must have get_all_verbs method")

                logger.info("Loading verbs into cache...")
                verbs = await repository.get_all_verbs(limit=10000)

                self._verbs_by_id.clear()
                self._verbs_by_key.clear()
                self._verbs_by_language.clear()

                for verb in verbs:
                    self._add_verb_to_indexes(verb)

                self._loaded = True
                logger.info(
                    f"✅ Loaded {len(verbs)} verbs into cache "
                    f"({len(self._verbs_by_language)} languages)"
                )

    def _add_verb_to_indexes(self, verb: Verb):
        """Add a verb to all indexes (internal helper)."""
        # Primary index
        self._verbs_by_id[verb.id] = verb

        # Secondary index
        key = (
            verb.infinitive,
            verb.auxiliary.value,
            verb.reflexive,
            verb.target_language_code,
        )
        self._verbs_by_key[key] = verb

        # Language index
        if verb.target_language_code not in self._verbs_by_language:
            self._verbs_by_language[verb.target_language_code] = []
        self._verbs_by_language[verb.target_language_code].append(verb)

    def _remove_verb_from_indexes(self, verb: Verb):
        """Remove a verb from all indexes (internal helper)."""
        # Primary index
        self._verbs_by_id.pop(verb.id, None)

        # Secondary index
        key = (
            verb.infinitive,
            verb.auxiliary.value,
            verb.reflexive,
            verb.target_language_code,
        )
        self._verbs_by_key.pop(key, None)

        # Language index
        if verb.target_language_code in self._verbs_by_language:
            lang_list = self._verbs_by_language[verb.target_language_code]
            self._verbs_by_language[verb.target_language_code] = [
                v for v in lang_list if v.id != verb.id
            ]

    async def get_by_id(self, verb_id: UUID) -> Verb | None:
        """Get a verb by ID from cache."""
        if not self._loaded:
            self._misses += 1
            return None

        verb = self._verbs_by_id.get(verb_id)
        if verb:
            self._hits += 1
        else:
            self._misses += 1
        return verb

    async def get_by_infinitive(
        self,
        infinitive: str,
        auxiliary: str,
        reflexive: bool,
        target_language_code: str,
    ) -> Verb | None:
        """Get a verb by its unique key from cache."""
        if not self._loaded:
            self._misses += 1
            return None

        key = (infinitive, auxiliary, reflexive, target_language_code)
        verb = self._verbs_by_key.get(key)
        if verb:
            self._hits += 1
        else:
            self._misses += 1
        return verb

    async def get_by_infinitive_simple(
        self, infinitive: str, target_language_code: str = "eng"
    ) -> Verb | None:
        """
        Get a verb by infinitive alone, without needing auxiliary/reflexive parameters.

        For reflexive verbs, the infinitive should include "se " prefix (e.g., "se coucher").
        For non-reflexive verbs, use the base infinitive (e.g., "coucher", "appeler").

        Handles both reflexive and non-reflexive forms of the same verb (e.g., "appeler" vs "se appeler").
        """
        if not self._loaded:
            self._misses += 1
            return None

        # Check if this is a reflexive verb (starts with "se ")
        is_reflexive_query = infinitive.startswith("se ")
        base_infinitive = infinitive[3:] if is_reflexive_query else infinitive

        # Search through all verbs for this language
        verbs = self._verbs_by_language.get(target_language_code, [])
        for verb in verbs:
            # Match based on base infinitive and reflexive flag
            if (
                verb.infinitive == base_infinitive
                and verb.reflexive == is_reflexive_query
            ):
                self._hits += 1
                return verb

        self._misses += 1
        return None

    async def get_all_by_language(self, target_language_code: str) -> list[Verb]:
        """Get all verbs for a language from cache."""
        if not self._loaded:
            return []

        verbs = self._verbs_by_language.get(target_language_code, [])
        if verbs:
            self._hits += 1
        return verbs.copy()  # Return a copy to prevent external modification

    async def get_random_verb(self, target_language_code: str = "eng") -> Verb | None:
        """Get a random verb from cache for the specified language."""
        if not self._loaded:
            self._misses += 1
            return None

        verbs = self._verbs_by_language.get(target_language_code, [])
        if not verbs:
            self._misses += 1
            return None

        import random

        self._hits += 1
        return random.choice(verbs)

    async def refresh_verb(self, verb: Verb):
        """Add or update a verb in the cache."""
        async with self._lock:
            # Remove old version if it exists
            if verb.id in self._verbs_by_id:
                old_verb = self._verbs_by_id[verb.id]
                self._remove_verb_from_indexes(old_verb)

            # Add new version
            self._add_verb_to_indexes(verb)
            logger.debug(f"Refreshed verb {verb.infinitive} in cache")

    async def invalidate_verb(self, verb_id: UUID):
        """Remove a verb from the cache."""
        async with self._lock:
            if verb_id in self._verbs_by_id:
                verb = self._verbs_by_id[verb_id]
                self._remove_verb_from_indexes(verb)
                logger.debug(f"Invalidated verb {verb_id} from cache")

    async def reload(self, repository):
        """Reload all verbs from database (for NOTIFY/LISTEN)."""
        logger.info("Reloading verb cache from database...")
        await self.load(repository)

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0

        return {
            "loaded": self._loaded,
            "total_verbs": len(self._verbs_by_id),
            "languages": len(self._verbs_by_language),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2f}%",
        }


# Global singleton instance
verb_cache = VerbCache()
