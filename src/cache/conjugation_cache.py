"""Redis-backed cache for conjugations."""

import logging

import redis.asyncio as aioredis
from opentelemetry import trace

from src.schemas.verbs import Conjugation, Tense

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class ConjugationCache:
    """
    Redis-backed cache for conjugations.

    Uses Redis for:
    - Primary index: conj:{infinitive}:{auxiliary}:{reflexive}:{tense} -> Conjugation JSON
    - Verb set: conj:verb:{infinitive}:{auxiliary}:{reflexive} -> Set of tense values

    This is a thin wrapper around Redis - no in-memory state is kept.
    Create instances as needed via dependency injection.

    Args:
        redis_client: The Redis client to use for storage.
        namespace: Optional namespace prefix for key isolation (useful for testing).
    """

    BASE_PREFIX = "conj"

    def __init__(self, redis_client: aioredis.Redis, namespace: str = ""):
        self._redis = redis_client
        self._loaded = False
        self._namespace = namespace
        self.PREFIX = f"{namespace}{self.BASE_PREFIX}" if namespace else self.BASE_PREFIX

        # Metrics (per-instance, mainly for debugging)
        self._hits = 0
        self._misses = 0
        self._conjugation_count = 0
        self._verb_count = 0

    def _conj_key(
        self, infinitive: str, auxiliary: str, reflexive: bool, tense: str
    ) -> str:
        """Key for conjugation lookup."""
        return f"{self.PREFIX}:{infinitive}:{auxiliary}:{reflexive}:{tense}"

    def _verb_set_key(self, infinitive: str, auxiliary: str, reflexive: bool) -> str:
        """Key for set of tenses for a verb."""
        return f"{self.PREFIX}:verb:{infinitive}:{auxiliary}:{reflexive}"

    async def load(self, repository) -> None:
        """Load all conjugations into Redis cache at startup."""
        with tracer.start_as_current_span("conjugation_cache.load"):
            if not hasattr(repository, "get_all_conjugations"):
                raise TypeError("Repository must have get_all_conjugations method")

            logger.info("Loading conjugations into Redis cache...")

            # Fetch all conjugations in a single query
            conjugations = await repository.get_all_conjugations(limit=10000)

            # Clear existing conjugation keys
            await self._clear_cache()

            # Track unique verbs
            verbs = set()

            # Use pipeline for batch operations
            pipe = self._redis.pipeline()

            for conj in conjugations:
                key = self._conj_key(
                    conj.infinitive,
                    conj.auxiliary.value,
                    conj.reflexive,
                    conj.tense.value,
                )
                verb_set_key = self._verb_set_key(
                    conj.infinitive, conj.auxiliary.value, conj.reflexive
                )

                # Store conjugation JSON
                pipe.set(key, conj.model_dump_json())

                # Add tense to verb's set
                pipe.sadd(verb_set_key, conj.tense.value)

                verbs.add((conj.infinitive, conj.auxiliary.value, conj.reflexive))

            await pipe.execute()

            self._loaded = True
            self._conjugation_count = len(conjugations)
            self._verb_count = len(verbs)
            logger.info(
                f"✅ Loaded {len(conjugations)} conjugations into Redis cache "
                f"({len(verbs)} unique verbs)"
            )

    async def _clear_cache(self) -> None:
        """Clear all conjugation cache keys using SCAN (non-blocking)."""
        cursor = 0
        while True:
            cursor, keys = await self._redis.scan(
                cursor, match=f"{self.PREFIX}:*", count=100
            )
            if keys:
                await self._redis.delete(*keys)
            if cursor == 0:
                break

    async def is_loaded(self) -> bool:
        """Check if cache has data by checking if any conjugation keys exist."""
        cursor, keys = await self._redis.scan(0, match=f"{self.PREFIX}:*", count=1)
        return len(keys) > 0

    async def get_conjugation(
        self,
        infinitive: str,
        auxiliary: str,
        reflexive: bool,
        tense: Tense,
    ) -> Conjugation | None:
        """Get a specific conjugation from cache."""
        key = self._conj_key(infinitive, auxiliary, reflexive, tense.value)
        data = await self._redis.get(key)

        if data:
            self._hits += 1
            return Conjugation.model_validate_json(data)

        self._misses += 1
        return None

    async def get_conjugations_for_verb(
        self,
        infinitive: str,
        auxiliary: str,
        reflexive: bool,
    ) -> list[Conjugation]:
        """Get all conjugations for a verb from cache."""
        verb_set_key = self._verb_set_key(infinitive, auxiliary, reflexive)

        # Get all tenses for this verb
        tenses = await self._redis.smembers(verb_set_key)
        if not tenses:
            return []

        # Fetch all conjugations in parallel using pipeline
        pipe = self._redis.pipeline()
        for tense in tenses:
            key = self._conj_key(infinitive, auxiliary, reflexive, tense)
            pipe.get(key)

        results = await pipe.execute()

        conjugations = []
        for data in results:
            if data:
                conjugations.append(Conjugation.model_validate_json(data))

        if conjugations:
            self._hits += 1

        return conjugations

    async def refresh_conjugation(self, conjugation: Conjugation) -> None:
        """Add or update a conjugation in the cache."""
        key = self._conj_key(
            conjugation.infinitive,
            conjugation.auxiliary.value,
            conjugation.reflexive,
            conjugation.tense.value,
        )
        verb_set_key = self._verb_set_key(
            conjugation.infinitive, conjugation.auxiliary.value, conjugation.reflexive
        )

        pipe = self._redis.pipeline()
        pipe.set(key, conjugation.model_dump_json())
        pipe.sadd(verb_set_key, conjugation.tense.value)
        await pipe.execute()

        logger.debug(
            f"Refreshed conjugation {conjugation.infinitive} "
            f"({conjugation.tense.value}) in cache"
        )

    async def invalidate_verb_conjugations(
        self,
        infinitive: str,
        auxiliary: str,
        reflexive: bool,
    ) -> None:
        """Remove all conjugations for a verb from cache."""
        verb_set_key = self._verb_set_key(infinitive, auxiliary, reflexive)

        # Get all tenses for this verb
        tenses = await self._redis.smembers(verb_set_key)

        if tenses:
            pipe = self._redis.pipeline()

            # Delete each conjugation
            for tense in tenses:
                key = self._conj_key(infinitive, auxiliary, reflexive, tense)
                pipe.delete(key)

            # Delete the verb set
            pipe.delete(verb_set_key)

            await pipe.execute()
            logger.debug(f"Invalidated conjugations for {infinitive} from cache")

    async def reload(self, repository) -> None:
        """Reload all conjugations from database."""
        logger.info("Reloading conjugation cache from database...")
        await self.load(repository)

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0

        return {
            "loaded": self._loaded,
            "total_conjugations": self._conjugation_count,
            "unique_verbs": self._verb_count,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2f}%",
        }
