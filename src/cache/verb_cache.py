"""Redis-backed cache for verbs with multiple access patterns."""

import logging
import random
from uuid import UUID

import redis.asyncio as aioredis
from opentelemetry import trace

from src.schemas.verbs import Verb

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class VerbCache:
    """
    Redis-backed cache for verbs with multiple indexes for different access patterns.

    Uses Redis for:
    - Primary index: verb:{id} -> verb JSON
    - Language sets: verb:lang:{code}:all -> Set of verb IDs (non-test only)
    - COD filter: verb:lang:{code}:cod -> Set of verb IDs that can have COD
    - COI filter: verb:lang:{code}:coi -> Set of verb IDs that can have COI

    This is a thin wrapper around Redis - no in-memory state is kept.
    Create instances as needed via dependency injection.

    Args:
        redis_client: The Redis client to use for storage.
        namespace: Optional namespace prefix for key isolation (useful for testing).
    """

    BASE_PREFIX = "verb"

    def __init__(self, redis_client: aioredis.Redis, namespace: str = ""):
        self._redis = redis_client
        self._loaded = False
        self._namespace = namespace
        self.PREFIX = f"{namespace}{self.BASE_PREFIX}" if namespace else self.BASE_PREFIX

        # Metrics (per-instance, mainly for debugging)
        self._hits = 0
        self._misses = 0
        self._verb_count = 0
        self._language_count = 0

    def _id_key(self, verb_id: UUID) -> str:
        """Key for verb lookup by ID."""
        return f"{self.PREFIX}:id:{verb_id}"

    def _lang_all_key(self, lang: str) -> str:
        """Key for set of all verb IDs for a language (non-test only)."""
        return f"{self.PREFIX}:lang:{lang}:all"

    def _lang_cod_key(self, lang: str) -> str:
        """Key for set of verb IDs that can have COD."""
        return f"{self.PREFIX}:lang:{lang}:cod"

    def _lang_coi_key(self, lang: str) -> str:
        """Key for set of verb IDs that can have COI."""
        return f"{self.PREFIX}:lang:{lang}:coi"

    async def load(self, repository) -> None:
        """Load all verbs into Redis cache at startup."""
        with tracer.start_as_current_span("verb_cache.load"):
            if not hasattr(repository, "get_all_verbs"):
                raise TypeError("Repository must have get_all_verbs method")

            logger.info("Loading verbs into Redis cache...")
            verbs = await repository.get_all_verbs()

            # Clear existing verb keys (use SCAN to avoid blocking)
            await self._clear_cache()

            # Track languages for stats
            languages = set()

            # Use pipeline for batch operations
            pipe = self._redis.pipeline()

            for verb in verbs:
                verb_id_str = str(verb.id)
                lang = verb.target_language_code

                # Store verb JSON by ID
                pipe.set(self._id_key(verb.id), verb.model_dump_json())

                # Add to language sets (exclude test verbs from random selection)
                if not verb.is_test:
                    pipe.sadd(self._lang_all_key(lang), verb_id_str)

                    if verb.can_have_cod:
                        pipe.sadd(self._lang_cod_key(lang), verb_id_str)

                    if verb.can_have_coi:
                        pipe.sadd(self._lang_coi_key(lang), verb_id_str)

                languages.add(lang)

            await pipe.execute()

            self._loaded = True
            self._verb_count = len(verbs)
            self._language_count = len(languages)
            logger.info(f"✅ Loaded {len(verbs)} verbs into Redis cache")

    async def _clear_cache(self) -> None:
        """Clear all verb cache keys using SCAN (non-blocking)."""
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
        """Check if cache has data by checking if any verb keys exist."""
        cursor, keys = await self._redis.scan(0, match=f"{self.PREFIX}:id:*", count=1)
        return len(keys) > 0

    async def get_by_id(self, verb_id: UUID) -> Verb | None:
        """Get a verb by ID from cache."""
        data = await self._redis.get(self._id_key(verb_id))

        if data:
            self._hits += 1
            return Verb.model_validate_json(data)

        self._misses += 1
        return None

    async def get_random_verb(
        self,
        target_language_code: str = "eng",
        requires_cod: bool = False,
        requires_coi: bool = False,
    ) -> Verb | None:
        """Get a random verb from cache for the specified language.

        Args:
            target_language_code: Language code for the verb
            requires_cod: If True, only return verbs that can have direct objects
            requires_coi: If True, only return verbs that can have indirect objects

        Excludes test verbs (is_test=True) from selection.
        """
        # Determine which sets to intersect
        sets_to_intersect = [self._lang_all_key(target_language_code)]

        if requires_cod:
            sets_to_intersect.append(self._lang_cod_key(target_language_code))

        if requires_coi:
            sets_to_intersect.append(self._lang_coi_key(target_language_code))

        # Get random verb ID from intersection
        if len(sets_to_intersect) == 1:
            # No filtering needed, use SRANDMEMBER directly
            verb_id_str = await self._redis.srandmember(sets_to_intersect[0])
        else:
            # Need to intersect, then pick random
            members = await self._redis.sinter(*sets_to_intersect)
            if not members:
                self._misses += 1
                return None
            verb_id_str = random.choice(list(members))

        if not verb_id_str:
            self._misses += 1
            return None

        # Fetch the full verb
        verb = await self.get_by_id(UUID(verb_id_str))
        if verb:
            return verb

        self._misses += 1
        return None

    async def refresh_verb(self, verb: Verb) -> None:
        """Add or update a verb in the cache."""
        verb_id_str = str(verb.id)
        lang = verb.target_language_code

        # Check if verb already exists (for proper set management)
        existing_data = await self._redis.get(self._id_key(verb.id))
        if existing_data:
            old_verb = Verb.model_validate_json(existing_data)
            # Remove from old language sets if language changed
            if old_verb.target_language_code != lang:
                old_lang = old_verb.target_language_code
                await self._redis.srem(self._lang_all_key(old_lang), verb_id_str)
                await self._redis.srem(self._lang_cod_key(old_lang), verb_id_str)
                await self._redis.srem(self._lang_coi_key(old_lang), verb_id_str)

        pipe = self._redis.pipeline()

        # Store verb JSON
        pipe.set(self._id_key(verb.id), verb.model_dump_json())

        # Update language sets (exclude test verbs)
        if not verb.is_test:
            pipe.sadd(self._lang_all_key(lang), verb_id_str)

            # Update COD set
            if verb.can_have_cod:
                pipe.sadd(self._lang_cod_key(lang), verb_id_str)
            else:
                pipe.srem(self._lang_cod_key(lang), verb_id_str)

            # Update COI set
            if verb.can_have_coi:
                pipe.sadd(self._lang_coi_key(lang), verb_id_str)
            else:
                pipe.srem(self._lang_coi_key(lang), verb_id_str)
        else:
            # Test verb - remove from all selection sets
            pipe.srem(self._lang_all_key(lang), verb_id_str)
            pipe.srem(self._lang_cod_key(lang), verb_id_str)
            pipe.srem(self._lang_coi_key(lang), verb_id_str)

        await pipe.execute()
        logger.debug(f"Refreshed verb {verb.infinitive} in cache")

    async def invalidate_verb(self, verb_id: UUID) -> None:
        """Remove a verb from the cache."""
        verb_id_str = str(verb_id)

        # Get verb first to know which sets to remove from
        data = await self._redis.get(self._id_key(verb_id))
        if data:
            verb = Verb.model_validate_json(data)
            lang = verb.target_language_code

            pipe = self._redis.pipeline()
            pipe.delete(self._id_key(verb_id))
            pipe.srem(self._lang_all_key(lang), verb_id_str)
            pipe.srem(self._lang_cod_key(lang), verb_id_str)
            pipe.srem(self._lang_coi_key(lang), verb_id_str)
            await pipe.execute()

            logger.debug(f"Invalidated verb {verb_id} from cache")

    async def reload(self, repository) -> None:
        """Reload all verbs from database."""
        logger.info("Reloading verb cache from database...")
        await self.load(repository)

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0

        return {
            "loaded": self._loaded,
            "total_verbs": self._verb_count,
            "languages": self._language_count,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2f}%",
        }
