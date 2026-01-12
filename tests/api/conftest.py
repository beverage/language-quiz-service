"""
Shared fixtures for API contract tests.

API tests focus on HTTP behavior, validation, and contracts.
They mock service dependencies to avoid database/event loop issues.

For real integration tests, use the service and repository test files.

Test Categories:
- Authentication tests (@pytest.mark.security): Use real auth, mock services
- Contract tests (@pytest.mark.integration): Mock auth AND services
- Validation tests (@pytest.mark.unit): Mock auth AND services
"""

from datetime import UTC, datetime
from uuid import uuid4

from src.schemas.sentences import (
    DirectObject,
    IndirectObject,
    Negation,
    Pronoun,
    Sentence,
)
from src.schemas.verbs import Tense, Verb

# =============================================================================
# Sample Data for Mocks
# =============================================================================


def create_sample_verb(infinitive: str = "parler", verb_id=None) -> Verb:
    """Create a sample verb for testing."""
    return Verb(
        id=verb_id or uuid4(),
        infinitive=infinitive,
        auxiliary="avoir",
        reflexive=False,
        target_language_code="eng",
        translation="to speak",
        past_participle="parlé",
        present_participle="parlant",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def create_sample_sentence(sentence_id=None, verb_id=None) -> Sentence:
    """Create a sample sentence for testing."""
    return Sentence(
        id=sentence_id or uuid4(),
        verb_id=verb_id or uuid4(),
        content="Je parle français.",
        translation="I speak French.",
        pronoun=Pronoun.FIRST_PERSON,
        tense=Tense.PRESENT,
        direct_object=DirectObject.NONE,
        indirect_object=IndirectObject.NONE,
        negation=Negation.NONE,
        is_correct=True,
        target_language_code="eng",
        explanation="Basic sentence in present tense.",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


# =============================================================================
# Mock Service Classes
# =============================================================================


class MockSentenceService:
    """Mock sentence service for API tests.

    Configure behavior by setting attributes:
    - return_sentences: List of sentences to return (default: one sample)
    - return_none: If True, return None for single-item lookups
    """

    def __init__(self):
        # Default: return one sample sentence
        sample = create_sample_sentence()
        self.sentences = {sample.id: sample}
        self.return_none = False

    async def get_random_sentence(self, verb_id=None, is_correct=None):
        """Mock get random sentence."""
        if self.return_none or not self.sentences:
            return None
        return list(self.sentences.values())[0]

    async def get_sentence(self, sentence_id):
        """Mock get sentence by ID."""
        if self.return_none:
            return None
        return self.sentences.get(sentence_id)

    async def get_sentences(self, verb_id=None, is_correct=None, limit=100):
        """Mock get sentences list."""
        return list(self.sentences.values())[:limit]

    async def get_sentences_by_verb(self, verb_id, limit=50):
        """Mock get sentences by verb."""
        return list(self.sentences.values())[:limit]

    async def delete_sentence(self, sentence_id):
        """Mock delete sentence."""
        if sentence_id in self.sentences:
            del self.sentences[sentence_id]
            return True
        from src.core.exceptions import NotFoundError

        raise NotFoundError(f"Sentence with ID {sentence_id} not found")

    async def count_sentences(self, verb_id=None, is_correct=None):
        """Mock count sentences."""
        return len(self.sentences)


class MockVerbService:
    """Mock verb service for API tests.

    Configure behavior by setting attributes:
    - verbs: Dict mapping infinitive -> Verb object
    - return_none: If True, return None for lookups
    """

    def __init__(self):
        # Default: return sample verbs
        sample = create_sample_verb("parler")
        self.verbs = {"parler": sample}
        self.verbs_by_id = {sample.id: sample}
        self.return_none = False

    async def get_random_verb(self, target_language_code="eng"):
        """Mock get random verb."""
        if self.return_none or not self.verbs:
            return None
        return list(self.verbs.values())[0]

    async def get_verb(self, verb_id):
        """Mock get verb by ID."""
        if self.return_none:
            return None
        return self.verbs_by_id.get(verb_id)

    async def get_verb_by_infinitive(
        self, infinitive, auxiliary=None, reflexive=None, target_language_code="eng"
    ):
        """Mock get verb by infinitive."""
        if self.return_none:
            return None
        return self.verbs.get(infinitive)

    async def get_verb_with_conjugations(
        self, infinitive, auxiliary=None, reflexive=False, target_language_code="eng"
    ):
        """Mock get verb with conjugations."""
        if self.return_none:
            return None
        verb = self.verbs.get(infinitive)
        if verb:
            from src.schemas.verbs import VerbWithConjugations

            return VerbWithConjugations(
                id=verb.id,
                infinitive=verb.infinitive,
                auxiliary=verb.auxiliary,
                reflexive=verb.reflexive,
                target_language_code=verb.target_language_code,
                translation=verb.translation,
                past_participle=verb.past_participle,
                present_participle=verb.present_participle,
                created_at=verb.created_at,
                updated_at=verb.updated_at,
                conjugations=[],
            )
        return None

    async def download_conjugations(self, infinitive, target_language_code="eng"):
        """Mock download conjugations."""
        verb = self.verbs.get(infinitive)
        if verb:
            from src.schemas.verbs import VerbWithConjugations

            return VerbWithConjugations(
                id=verb.id,
                infinitive=verb.infinitive,
                auxiliary=verb.auxiliary,
                reflexive=verb.reflexive,
                target_language_code=verb.target_language_code,
                translation=verb.translation,
                past_participle=verb.past_participle,
                present_participle=verb.present_participle,
                created_at=verb.created_at,
                updated_at=verb.updated_at,
                conjugations=[],
            )
        from src.core.exceptions import NotFoundError

        raise NotFoundError(f"Verb '{infinitive}' not found")


class MockProblemService:
    """Mock problem service for API tests.

    Configure behavior by setting attributes:
    - problems: Dict mapping problem_id -> problem object
    - return_none: If True, return None for lookups
    """

    def __init__(self):
        self.problems = {}
        self.return_none = False

    async def get_random_problem(self, filters=None):
        """Mock get random problem."""
        if self.return_none or not self.problems:
            return None
        return list(self.problems.values())[0]

    async def get_least_recently_served_problem(self, filters=None):
        """Mock get LRU problem for /random endpoint."""
        if self.return_none or not self.problems:
            return None
        return list(self.problems.values())[0]

    async def get_random_grammar_problem(
        self,
        grammatical_focus=None,
        tenses_used=None,
        topic_tags=None,
        target_language_code=None,
    ):
        """Mock get random grammar problem for /grammar/random endpoint."""
        if self.return_none or not self.problems:
            return None
        # Simple mock: return first problem if it matches filters (basic check)
        problem = list(self.problems.values())[0]
        if grammatical_focus and problem.metadata:
            problem_focus = problem.metadata.get("grammatical_focus", [])
            if not any(f in problem_focus for f in grammatical_focus):
                return None
        if tenses_used and problem.metadata:
            problem_tenses = problem.metadata.get("tenses_used", [])
            if not any(t in problem_tenses for t in tenses_used):
                return None
        return problem

    async def get_problem_by_id(self, problem_id):
        """Mock get problem by ID.

        Returns None for not found (API will convert to 404).
        """
        return self.problems.get(problem_id)

    async def get_problems(self, filters, include_statements=True):
        """Mock get problems list."""
        return list(self.problems.values()), len(self.problems)

    async def create_random_grammar_problem(self, **kwargs):
        """Mock create random grammar problem."""
        from src.core.exceptions import ServiceError

        raise ServiceError("Use async generation endpoint")

    async def close(self):
        """Mock close method."""
        pass


class MockQueueService:
    """Mock queue service for API contract tests.

    Records all publish calls for verification in tests.
    """

    def __init__(self):
        self.published_requests = []

    async def publish_problem_generation_request(
        self,
        constraints=None,
        focus=None,
        statement_count=4,
        topic_tags=None,
        count=1,
    ):
        """Mock publish that records calls and returns mock response."""
        self.published_requests.append(
            {
                "constraints": constraints,
                "focus": focus,
                "statement_count": statement_count,
                "topic_tags": topic_tags,
                "count": count,
            }
        )
        request_id = str(uuid4())  # Must be string for response schema
        return count, request_id

    async def close(self):
        """Mock close method."""
        pass
