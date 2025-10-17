"""In-memory cache for conjugations."""

import asyncio
import logging

from opentelemetry import trace

from src.schemas.verbs import Conjugation, Tense

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class ConjugationCache:
    """
    In-memory cache for conjugations.

    Indexed by (infinitive, auxiliary, reflexive, tense) for fast lookup.
    Also provides bulk lookup by verb.
    """

    def __init__(self):
        # Index: (infinitive, auxiliary, reflexive, tense) -> Conjugation
        self._conjugations: dict[tuple[str, str, bool, str], Conjugation] = {}

        # Index: (infinitive, auxiliary, reflexive) -> list[Conjugation]
        self._by_verb: dict[tuple[str, str, bool], list[Conjugation]] = {}

        self._loaded = False
        self._lock = asyncio.Lock()

        # Metrics
        self._hits = 0
        self._misses = 0

    async def load(self, repository):
        """Load all conjugations into cache at startup."""
        with tracer.start_as_current_span("conjugation_cache.load"):
            async with self._lock:
                # Duck typing: check for the methods we need instead of isinstance
                if not hasattr(repository, "get_all_verbs") or not hasattr(
                    repository, "get_conjugations"
                ):
                    raise TypeError(
                        "Repository must have get_all_verbs and get_conjugations methods"
                    )

                logger.info("Loading conjugations into cache...")

                # We need to load all verbs to get their conjugations
                verbs = await repository.get_all_verbs(limit=10000)

                self._conjugations.clear()
                self._by_verb.clear()

                conjugation_count = 0
                for verb in verbs:
                    conjugations = await repository.get_conjugations(
                        infinitive=verb.infinitive,
                        auxiliary=verb.auxiliary.value,
                        reflexive=verb.reflexive,
                    )

                    for conj in conjugations:
                        self._add_conjugation_to_indexes(conj)
                        conjugation_count += 1

                self._loaded = True
                logger.info(
                    f"✅ Loaded {conjugation_count} conjugations into cache "
                    f"({len(self._by_verb)} unique verbs)"
                )

    def _add_conjugation_to_indexes(self, conjugation: Conjugation):
        """Add a conjugation to all indexes (internal helper)."""
        # Primary index
        key = (
            conjugation.infinitive,
            conjugation.auxiliary.value,
            conjugation.reflexive,
            conjugation.tense.value,
        )
        self._conjugations[key] = conjugation

        # Verb index
        verb_key = (
            conjugation.infinitive,
            conjugation.auxiliary.value,
            conjugation.reflexive,
        )
        if verb_key not in self._by_verb:
            self._by_verb[verb_key] = []

        # Replace if already exists, otherwise append
        existing = [c for c in self._by_verb[verb_key] if c.tense != conjugation.tense]
        existing.append(conjugation)
        self._by_verb[verb_key] = existing

    def _remove_conjugation_from_indexes(self, conjugation: Conjugation):
        """Remove a conjugation from all indexes (internal helper)."""
        # Primary index
        key = (
            conjugation.infinitive,
            conjugation.auxiliary.value,
            conjugation.reflexive,
            conjugation.tense.value,
        )
        self._conjugations.pop(key, None)

        # Verb index
        verb_key = (
            conjugation.infinitive,
            conjugation.auxiliary.value,
            conjugation.reflexive,
        )
        if verb_key in self._by_verb:
            self._by_verb[verb_key] = [
                c for c in self._by_verb[verb_key] if c.tense != conjugation.tense
            ]

    async def get_conjugation(
        self,
        infinitive: str,
        auxiliary: str,
        reflexive: bool,
        tense: Tense,
    ) -> Conjugation | None:
        """Get a specific conjugation from cache."""
        if not self._loaded:
            self._misses += 1
            return None

        key = (infinitive, auxiliary, reflexive, tense.value)
        conj = self._conjugations.get(key)
        if conj:
            self._hits += 1
        else:
            self._misses += 1
        return conj

    async def get_conjugations_for_verb(
        self,
        infinitive: str,
        auxiliary: str,
        reflexive: bool,
    ) -> list[Conjugation]:
        """Get all conjugations for a verb from cache."""
        if not self._loaded:
            return []

        verb_key = (infinitive, auxiliary, reflexive)
        conjs = self._by_verb.get(verb_key, [])
        if conjs:
            self._hits += 1
        return conjs.copy()  # Return a copy to prevent external modification

    async def refresh_conjugation(self, conjugation: Conjugation):
        """Add or update a conjugation in the cache."""
        async with self._lock:
            # Remove old version if it exists
            self._remove_conjugation_from_indexes(conjugation)

            # Add new version
            self._add_conjugation_to_indexes(conjugation)
            logger.debug(
                f"Refreshed conjugation {conjugation.infinitive} "
                f"({conjugation.tense.value}) in cache"
            )

    async def invalidate_verb_conjugations(
        self,
        infinitive: str,
        auxiliary: str,
        reflexive: bool,
    ):
        """Remove all conjugations for a verb from cache."""
        async with self._lock:
            verb_key = (infinitive, auxiliary, reflexive)
            if verb_key in self._by_verb:
                conjugations = self._by_verb[verb_key]
                for conj in conjugations:
                    self._remove_conjugation_from_indexes(conj)
                logger.debug(f"Invalidated conjugations for {infinitive} from cache")

    async def reload(self, repository):
        """Reload all conjugations from database (for NOTIFY/LISTEN)."""
        logger.info("Reloading conjugation cache from database...")
        await self.load(repository)

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0

        return {
            "loaded": self._loaded,
            "total_conjugations": len(self._conjugations),
            "unique_verbs": len(self._by_verb),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2f}%",
        }


# Global singleton instance
conjugation_cache = ConjugationCache()
