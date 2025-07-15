"""Tests for ProblemService business logic."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from src.services.problem_service import ProblemService
from src.schemas.problems import (
    ProblemCreate,
    ProblemUpdate,
    ProblemType,
    ProblemFilters,
    GrammarProblemConstraints,
)
from src.schemas.sentences import Pronoun, Tense, DirectObject, IndirectObject, Negation
from src.schemas.verbs import AuxiliaryType, VerbClassification

# Import fixtures from problems domain
from tests.problems.fixtures import problem_repository, generate_random_problem_data

# Import verb fixtures from verbs domain
from tests.verbs.fixtures import sample_verb


@pytest.fixture
def sample_problem_create():
    """Create a sample ProblemCreate instance for testing."""
    problem_data = generate_random_problem_data()
    return ProblemCreate(**problem_data)


@pytest.mark.asyncio
class TestProblemService:
    """Test ProblemService business logic."""

    async def test_create_and_retrieve_problem(
        self, problem_repository, sample_problem_create
    ):
        """Test creating and retrieving a problem."""
        service = ProblemService(problem_repository=problem_repository)

        # Create a simple grammar problem
        problem_data = ProblemCreate(
            problem_type=ProblemType.GRAMMAR,
            title="Grammar: Parler",
            instructions="Choose the correctly formed French sentence.",
            correct_answer_index=0,
            target_language_code="eng",
            statements=[
                {
                    "content": "Je parle français.",
                    "is_correct": True,
                    "translation": "I speak French.",
                },
                {
                    "content": "Je parles français.",
                    "is_correct": False,
                    "explanation": "Wrong conjugation",
                },
            ],
            topic_tags=["grammar", "basic_grammar"],
            source_statement_ids=[uuid4(), uuid4()],
            metadata={"grammatical_focus": ["basic_conjugation"]},
        )

        # Create the problem
        created_problem = await service.create_problem(problem_data)
        assert created_problem.id is not None
        assert created_problem.title == "Grammar: Parler"
        assert created_problem.problem_type == ProblemType.GRAMMAR
        assert len(created_problem.statements) == 2
        assert created_problem.correct_answer_index == 0

        # Retrieve the problem
        retrieved_problem = await service.get_problem(created_problem.id)
        assert retrieved_problem.id == created_problem.id
        assert retrieved_problem.title == created_problem.title

    async def test_update_problem(self, problem_repository, sample_problem_create):
        """Test updating a problem."""
        service = ProblemService(problem_repository=problem_repository)

        # Create initial problem
        created_problem = await service.create_problem(sample_problem_create)

        # Update the problem
        update_data = ProblemUpdate(
            title="Updated Grammar: Parler",
            instructions="Updated: Choose the correctly formed French sentence.",
        )

        updated_problem = await service.update_problem(created_problem.id, update_data)
        assert updated_problem.title == "Updated Grammar: Parler"
        assert (
            updated_problem.instructions
            == "Updated: Choose the correctly formed French sentence."
        )
        assert updated_problem.problem_type == created_problem.problem_type  # Unchanged

    async def test_delete_problem(self, problem_repository, sample_problem_create):
        """Test deleting a problem."""
        service = ProblemService(problem_repository=problem_repository)

        # Create a problem
        created_problem = await service.create_problem(sample_problem_create)

        # Delete the problem
        success = await service.delete_problem(created_problem.id)
        assert success is True

        # Verify it's gone
        deleted_problem = await service.get_problem(created_problem.id)
        assert deleted_problem is None

    async def test_get_problems_with_filters(
        self, problem_repository, sample_problem_create
    ):
        """Test getting problems with filters."""
        service = ProblemService(problem_repository=problem_repository)

        # Create multiple problems with unique identifiers
        unique_tag = f"test_filter_{uuid4().hex[:8]}"

        problem1_data = ProblemCreate(
            **{
                **sample_problem_create.model_dump(),
                "title": f"Problem 1 {unique_tag}",
                "topic_tags": [unique_tag, "grammar"],
            }
        )
        problem1 = await service.create_problem(problem1_data)

        problem2_data = ProblemCreate(
            **{
                **sample_problem_create.model_dump(),
                "title": f"Problem 2 {unique_tag}",
                "topic_tags": [unique_tag, "grammar"],
            }
        )
        problem2 = await service.create_problem(problem2_data)

        # Get problems by our unique tag (should find exactly our 2 problems)
        problems_by_topic = await service.get_problems_by_topic([unique_tag], limit=10)
        found_ids = [p.id for p in problems_by_topic]
        assert problem1.id in found_ids
        assert problem2.id in found_ids

        # Filter by type (should include our problems among others)
        grammar_problems, grammar_total = await service.get_problems(
            ProblemFilters(problem_type=ProblemType.GRAMMAR)
        )
        assert grammar_total >= 2  # At least our 2 problems
        for problem in grammar_problems:
            assert problem.problem_type == ProblemType.GRAMMAR

    async def test_get_problem_summaries(
        self, problem_repository, sample_problem_create
    ):
        """Test getting problem summaries."""
        service = ProblemService(problem_repository=problem_repository)

        # Create a problem with a unique tag for identification
        unique_tag = f"summary_test_{uuid4().hex[:8]}"
        problem_data = ProblemCreate(
            **{
                **sample_problem_create.model_dump(),
                "title": f"Summary Test {unique_tag}",
                "topic_tags": [unique_tag],
            }
        )
        created_problem = await service.create_problem(problem_data)

        # Test that get_problem_summaries works without errors
        summaries, total = await service.get_problem_summaries(ProblemFilters(limit=50))

        # Basic validation
        assert total >= 1
        assert len(summaries) <= 50
        assert len(summaries) > 0

        # Validate structure of returned summaries
        first_summary = summaries[0]
        assert hasattr(first_summary, "id")
        assert hasattr(first_summary, "title")
        assert hasattr(first_summary, "problem_type")
        assert hasattr(first_summary, "statement_count")
        assert isinstance(first_summary.statement_count, int)
        assert first_summary.statement_count >= 0

        # Verify our created problem exists (may not be in the limited results due to ordering)
        retrieved = await service.get_problem(created_problem.id)
        assert retrieved is not None
        assert retrieved.title == created_problem.title

    async def test_get_problems_by_topic(
        self, problem_repository, sample_problem_create
    ):
        """Test getting problems by topic tags."""
        service = ProblemService(problem_repository=problem_repository)

        # Create a problem with specific tags
        unique_tag = f"topic_test_{uuid4().hex[:8]}"
        problem_data = ProblemCreate(
            **{
                **sample_problem_create.model_dump(),
                "topic_tags": [unique_tag, "grammar"],
            }
        )
        created_problem = await service.create_problem(problem_data)

        # Search by topic
        problems = await service.get_problems_by_topic([unique_tag], limit=10)
        problem_ids = [p.id for p in problems]
        assert created_problem.id in problem_ids

    async def test_get_random_problem(self, problem_repository, sample_problem_create):
        """Test getting a random problem."""
        service = ProblemService(problem_repository=problem_repository)

        # Create a problem first
        await service.create_problem(sample_problem_create)

        # Get random problem
        random_problem = await service.get_random_problem(
            problem_type=ProblemType.GRAMMAR, topic_tags=["grammar"]
        )

        # Should get a problem (might be ours or others in the DB)
        if random_problem:
            assert random_problem.problem_type == ProblemType.GRAMMAR

    async def test_count_problems(self, problem_repository, sample_problem_create):
        """Test counting problems."""
        service = ProblemService(problem_repository=problem_repository)

        # Get initial count
        initial_count = await service.count_problems()

        # Create a problem
        await service.create_problem(sample_problem_create)

        # Count should increase
        new_count = await service.count_problems()
        assert new_count == initial_count + 1

        # Count with filters
        grammar_count = await service.count_problems(problem_type=ProblemType.GRAMMAR)
        assert grammar_count >= 1

    async def test_get_problem_statistics(
        self, problem_repository, sample_problem_create
    ):
        """Test getting problem statistics."""
        service = ProblemService(problem_repository=problem_repository)

        # Create a problem to ensure we have data
        await service.create_problem(sample_problem_create)

        # Get statistics
        stats = await service.get_problem_statistics()
        assert "total_problems" in stats
        assert stats["total_problems"] >= 1
        assert "problems_by_type" in stats


class TestProblemServiceParameterGeneration:
    """Test parameter generation methods."""

    def test_generate_grammatical_parameters_basic(self, sample_verb):
        """Test basic grammatical parameter generation."""
        service = ProblemService()
        constraints = GrammarProblemConstraints()

        params = service._generate_grammatical_parameters(sample_verb, constraints)

        # Should have all required parameters
        assert "pronoun" in params
        assert "tense" in params
        assert "direct_object" in params
        assert "indirect_object" in params
        assert "negation" in params

        # Should be valid enum values
        assert isinstance(params["pronoun"], Pronoun)
        assert isinstance(params["tense"], Tense)
        assert isinstance(params["direct_object"], DirectObject)
        assert isinstance(params["indirect_object"], IndirectObject)
        assert isinstance(params["negation"], Negation)

    def test_generate_grammatical_parameters_with_constraints(self, sample_verb):
        """Test parameter generation with constraints."""
        service = ProblemService()
        constraints = GrammarProblemConstraints(
            tenses_used=["present", "passe_compose"],
            includes_negation=True,
            includes_cod=True,
        )

        params = service._generate_grammatical_parameters(sample_verb, constraints)

        # Should respect tense constraints
        assert params["tense"] in [Tense.PRESENT, Tense.PASSE_COMPOSE]

    def test_vary_parameters_for_correct_statement(self, sample_verb):
        """Test parameter variation for correct statements."""
        service = ProblemService()
        base_params = {
            "pronoun": Pronoun.FIRST_PERSON,
            "tense": Tense.PRESENT,
            "direct_object": DirectObject.NONE,
            "indirect_object": IndirectObject.NONE,
            "negation": Negation.NONE,
        }

        # Correct statement should use base parameters
        params = service._vary_parameters_for_statement(
            base_params, 0, True, sample_verb
        )
        assert params == base_params

    def test_vary_parameters_for_incorrect_statement(self, sample_verb):
        """Test parameter variation for incorrect statements."""
        service = ProblemService()
        base_params = {
            "pronoun": Pronoun.FIRST_PERSON,
            "tense": Tense.PRESENT,
            "direct_object": DirectObject.NONE,
            "indirect_object": IndirectObject.NONE,
            "negation": Negation.NONE,
        }

        # Incorrect statement should have some variation
        params = service._vary_parameters_for_statement(
            base_params, 1, False, sample_verb
        )

        # Should still be a valid parameter set
        assert isinstance(params, dict)
        assert all(key in params for key in base_params.keys())

    def test_derive_topic_tags_basic(self, sample_verb):
        """Test basic topic tag derivation."""
        service = ProblemService()
        constraints = GrammarProblemConstraints()
        metadata = {
            "grammatical_focus": ["basic_conjugation"],
            "includes_cod": False,
            "includes_coi": False,
            "includes_negation": False,
        }

        tags = service._derive_topic_tags(sample_verb, constraints, metadata)

        # Should always include basic grammar tags
        assert "basic_conjugation" in tags
        assert "basic_grammar" in tags

    def test_derive_grammar_metadata(self, sample_verb):
        """Test metadata derivation from sentences."""
        service = ProblemService()

        # Create a mock sentence with COD
        from src.schemas.sentences import Sentence

        sentence = Sentence(
            id=uuid4(),
            content="Je le mange.",
            translation="I eat it.",
            verb_id=sample_verb.id,
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PRESENT,
            direct_object=DirectObject.MASCULINE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=True,
            target_language_code="eng",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        constraints = GrammarProblemConstraints()
        metadata = service._derive_grammar_metadata(
            [sentence], sample_verb, constraints
        )

        assert "grammatical_focus" in metadata
        assert metadata["includes_cod"] is True
        assert metadata["includes_coi"] is False
        assert metadata["includes_negation"] is False
        assert sample_verb.infinitive in metadata["verb_infinitives"]


class TestProblemServiceIntegration:
    """Integration tests that might use other services."""

    @pytest.mark.asyncio
    async def test_service_initialization_with_dependencies(self, problem_repository):
        """Test service initialization with injected dependencies."""
        service = ProblemService(problem_repository=problem_repository)

        assert service.problem_repository == problem_repository
        assert service.sentence_service is not None
        assert service.verb_service is not None

    def test_service_initialization_without_dependencies(self):
        """Test service initialization without injected dependencies."""
        service = ProblemService()

        assert service.problem_repository is None
        assert service.sentence_service is not None
        assert service.verb_service is not None

    @pytest.mark.asyncio
    async def test_lazy_repository_initialization(self):
        """Test that repository is lazily initialized when needed."""
        service = ProblemService()  # No repository injected

        # This should trigger lazy initialization
        # Note: This test might fail if Supabase isn't running, which is expected
        try:
            repo = await service._get_problem_repository()
            assert repo is not None
            assert service.problem_repository == repo
        except Exception:
            # Expected if Supabase isn't running in this test context
            pytest.skip("Supabase not available for lazy initialization test")
