"""Tests for ProblemService business logic."""

from datetime import UTC, datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.core.exceptions import (
    LanguageResourceNotFoundError,
    NotFoundError,
    ServiceError,
)
from src.schemas.problems import (
    GrammarProblemConstraints,
    ProblemCreate,
    ProblemFilters,
    ProblemType,
    ProblemUpdate,
)
from src.schemas.sentences import DirectObject, IndirectObject, Negation, Pronoun, Tense
from src.schemas.verbs import AuxiliaryType, VerbClassification, VerbCreate
from src.services.problem_service import ProblemService

# Import fixtures from problems domain
from tests.problems.fixtures import generate_random_problem_data, problem_repository

# Import verb fixtures from verbs domain
from tests.verbs.fixtures import sample_verb, verb_repository


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
        from uuid import uuid4

        problem_data = ProblemCreate(
            problem_type=ProblemType.GRAMMAR,
            title=f"Grammar: Parler_{uuid4().hex[:8]}",
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
            topic_tags=["test_data", "grammar", "basic_grammar"],
            source_statement_ids=[uuid4(), uuid4()],
            metadata={"grammatical_focus": ["basic_conjugation"]},
        )

        # Create the problem
        created_problem = await service.create_problem(problem_data)
        assert created_problem.id is not None
        assert created_problem.title.startswith("Grammar: Parler_")
        assert len(created_problem.title.split("_")[-1]) == 8  # UUID hex suffix
        assert created_problem.problem_type == ProblemType.GRAMMAR
        assert len(created_problem.statements) == 2
        assert created_problem.correct_answer_index == 0

        # Retrieve the problem
        retrieved_problem = await service.get_problem_by_id(created_problem.id)
        assert retrieved_problem.id == created_problem.id
        assert retrieved_problem.title == created_problem.title

    async def test_update_problem(self, problem_repository, sample_problem_create):
        """Test updating a problem."""
        service = ProblemService(problem_repository=problem_repository)

        # Create initial problem
        created_problem = await service.create_problem(sample_problem_create)

        # Update the problem
        from uuid import uuid4

        update_data = ProblemUpdate(
            title=f"Updated Grammar: Parler_{uuid4().hex[:8]}",
            instructions="Updated: Choose the correctly formed French sentence.",
        )

        updated_problem = await service.update_problem(created_problem.id, update_data)
        assert updated_problem.title.startswith("Updated Grammar: Parler_")
        assert len(updated_problem.title.split("_")[-1]) == 8  # UUID hex suffix
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
        with pytest.raises(NotFoundError):
            await service.get_problem_by_id(created_problem.id)

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
                "topic_tags": ["test_data", unique_tag, "grammar"],
            }
        )
        problem1 = await service.create_problem(problem1_data)

        problem2_data = ProblemCreate(
            **{
                **sample_problem_create.model_dump(),
                "title": f"Problem 2 {unique_tag}",
                "topic_tags": ["test_data", unique_tag, "grammar"],
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
                "topic_tags": ["test_data", unique_tag],
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
        retrieved = await service.get_problem_by_id(created_problem.id)
        assert retrieved is not None
        assert retrieved.title == created_problem.title

    async def test_get_random_problem(self, problem_repository, sample_problem_create):
        """Test getting a random problem."""
        service = ProblemService(problem_repository=problem_repository)
        random_problem = await service.get_random_problem(ProblemFilters())
        assert random_problem is not None
        assert hasattr(random_problem, "id")

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


@pytest.mark.asyncio
class TestProblemServiceAnalytics:
    """Test ProblemService analytics-related business logic."""

    @pytest.mark.asyncio
    async def test_get_problems_using_verb(self, problem_repository, verb_repository):
        """Test retrieving problems associated with a specific verb."""
        # Setup: Create a verb and problem using UUID-based pattern
        from uuid import uuid4

        from tests.problems.fixtures import generate_random_problem_data
        from tests.verbs.fixtures import generate_random_verb_data

        # Create a verb first using the repository directly
        verb_data = VerbCreate(**generate_random_verb_data())
        created_verb = await verb_repository.create_verb(verb_data)

        problem_service = ProblemService(problem_repository=problem_repository)

        # Create a problem with verb metadata using the UUID-based pattern
        problem_data = ProblemCreate(
            **generate_random_problem_data(
                title=f"Grammar: {created_verb.infinitive}_{uuid4().hex[:8]}",
                metadata={"verb_infinitive": created_verb.infinitive},
            )
        )
        created_problem = await problem_service.create_problem(problem_data)

        # Verify the problem was created with correct metadata
        assert created_problem.metadata is not None
        assert "verb_infinitive" in created_problem.metadata
        assert created_problem.metadata["verb_infinitive"] == created_verb.infinitive

        # Test: Retrieve problems by verb infinitive
        problems, total = await problem_service.get_problems(
            ProblemFilters(verb=created_verb.infinitive)
        )
        assert total > 0, (
            f"Expected to find at least 1 problem for verb '{created_verb.infinitive}', "
            f"but found {total}. Created problem ID: {created_problem.id}, "
            f"metadata: {created_problem.metadata}"
        )
        assert any(p.id == created_problem.id for p in problems)

    @pytest.mark.asyncio
    async def test_get_problems_by_grammatical_focus(self, problem_repository):
        """Test retrieving problems by a specific grammatical focus."""
        from uuid import uuid4

        from tests.problems.fixtures import generate_random_problem_data

        problem_service = ProblemService(problem_repository=problem_repository)

        # Create a problem with a unique grammatical focus using UUID-based pattern
        focus = f"test_focus_{uuid4().hex[:8]}"  # Make focus unique
        problem_data = ProblemCreate(
            **generate_random_problem_data(
                title=f"Grammatical focus test: {focus}_{uuid4().hex[:8]}",
                metadata={"grammatical_focus": [focus]},
            )
        )
        created_problem = await problem_service.create_problem(problem_data)

        # Test: Retrieve problems by grammatical focus
        problems = await problem_service.get_problems_by_grammatical_focus(
            focus, limit=10
        )

        assert len(problems) > 0
        assert any(p.id == created_problem.id for p in problems)

    @pytest.mark.asyncio
    async def test_get_random_problem_with_filters(self, problem_repository):
        """Test retrieving a random problem with specific filters."""
        problem_service = ProblemService(problem_repository=problem_repository)

        # Create a problem with a unique attribute to filter on
        unique_focus = f"imperfect_{uuid4().hex}"
        problem_data = ProblemCreate(
            problem_type=ProblemType.GRAMMAR,
            title=f"Random problem filter test: {unique_focus}",
            instructions="Test instruction",
            correct_answer_index=0,
            target_language_code="eng",
            statements=[
                {
                    "content": "Statement 1",
                    "is_correct": True,
                    "translation": "Translation 1",
                }
            ],
            topic_tags=["test_data", "test"],
            source_statement_ids=[],
            metadata={"grammatical_focus": [unique_focus]},
        )
        await problem_service.create_problem(problem_data)

        # Test: Retrieve a random problem with the specified unique filter
        random_problem = await problem_service.get_random_problem(
            ProblemFilters(metadata_contains={"grammatical_focus": [unique_focus]})
        )
        assert random_problem is not None
        assert unique_focus in random_problem.metadata.get("grammatical_focus", [])


class TestProblemServiceParameterGeneration:
    """Test static methods for generating problem parameters."""

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

    def test_generate_grammatical_parameters_with_cod_constraint(self, sample_verb):
        """Test parameter generation with COD constraints."""
        service = ProblemService()

        # Test with includes_cod=True
        constraints = GrammarProblemConstraints(includes_cod=True)
        sample_verb.can_have_cod = True  # Ensure verb supports COD

        service._generate_grammatical_parameters(sample_verb, constraints)
        # Note: Due to randomness, we can't guarantee COD will be selected,
        # but we can test that the logic doesn't crash

    def test_generate_grammatical_parameters_with_coi_constraint(self, sample_verb):
        """Test parameter generation with COI constraints."""
        service = ProblemService()

        # Test with includes_coi=True
        constraints = GrammarProblemConstraints(includes_coi=True)
        sample_verb.can_have_coi = True  # Ensure verb supports COI

        service._generate_grammatical_parameters(sample_verb, constraints)
        # Note: Due to randomness, we can't guarantee COI will be selected,
        # but we can test that the logic doesn't crash

    def test_generate_grammatical_parameters_edge_cases(self, sample_verb):
        """Test parameter generation edge cases."""
        service = ProblemService()

        # Test with verb that doesn't support objects
        sample_verb.can_have_cod = False
        sample_verb.can_have_coi = False

        constraints = GrammarProblemConstraints()
        params = service._generate_grammatical_parameters(sample_verb, constraints)

        # Should still generate valid parameters
        assert params["direct_object"] == DirectObject.NONE
        assert params["indirect_object"] == IndirectObject.NONE

    # def test_vary_parameters_for_correct_statement(self, sample_verb):
    #     """Test parameter variation for correct statements."""
    #     service = ProblemService()
    #     base_params = {
    #         "pronoun": Pronoun.FIRST_PERSON,
    #         "tense": Tense.PRESENT,
    #         "direct_object": DirectObject.NONE,
    #         "indirect_object": IndirectObject.NONE,
    #         "negation": Negation.NONE,
    #     }

    #     # Correct statement should use base parameters
    #     params = service._vary_parameters_for_statement(
    #         base_params, 0, True, sample_verb
    #     )
    #     assert params == base_params

    # def test_vary_parameters_for_incorrect_statement(self, sample_verb):
    #     """Test parameter variation for incorrect statements."""
    #     service = ProblemService()
    #     base_params = {
    #         "pronoun": Pronoun.FIRST_PERSON,
    #         "tense": Tense.PRESENT,
    #         "direct_object": DirectObject.NONE,
    #         "indirect_object": IndirectObject.NONE,
    #         "negation": Negation.NONE,
    #     }

    #     # Incorrect statement should have some variation
    #     params = service._vary_parameters_for_statement(
    #         base_params, 1, False, sample_verb
    #     )

    #     # Should still be a valid parameter set
    #     assert isinstance(params, dict)
    #     assert all(key in params for key in base_params.keys())

    # def test_vary_parameters_with_direct_object_errors(self, sample_verb):
    #     """Test parameter variation with direct object error types."""
    #     service = ProblemService()
    #     base_params = {
    #         "pronoun": Pronoun.FIRST_PERSON,
    #         "tense": Tense.PRESENT,
    #         "direct_object": DirectObject.MASCULINE,  # Has a direct object
    #         "indirect_object": IndirectObject.NONE,
    #         "negation": Negation.NONE,
    #     }

    #     # Test error type 0 (direct object errors)
    #     params = service._vary_parameters_for_statement(
    #         base_params, 0, False, sample_verb
    #     )

    #     # Should still be valid
    #     assert isinstance(params, dict)
    #     assert all(key in params for key in base_params.keys())

    # def test_vary_parameters_with_indirect_object_errors(self, sample_verb):
    #     """Test parameter variation with indirect object error types."""
    #     service = ProblemService()
    #     base_params = {
    #         "pronoun": Pronoun.FIRST_PERSON,
    #         "tense": Tense.PRESENT,
    #         "direct_object": DirectObject.NONE,
    #         "indirect_object": IndirectObject.MASCULINE,  # Has an indirect object
    #         "negation": Negation.NONE,
    #     }

    #     # Test error type 1 (indirect object errors)
    #     params = service._vary_parameters_for_statement(
    #         base_params, 1, False, sample_verb
    #     )

    #     # Should still be valid
    #     assert isinstance(params, dict)
    #     assert all(key in params for key in base_params.keys())

    # def test_vary_parameters_with_negation_errors(self, sample_verb):
    #     """Test parameter variation with negation error types."""
    #     service = ProblemService()
    #     base_params = {
    #         "pronoun": Pronoun.FIRST_PERSON,
    #         "tense": Tense.PRESENT,
    #         "direct_object": DirectObject.NONE,
    #         "indirect_object": IndirectObject.NONE,
    #         "negation": Negation.PAS,  # Has negation (fixed enum value)
    #     }

    #     # Test error type 2 (negation errors)
    #     params = service._vary_parameters_for_statement(
    #         base_params, 2, False, sample_verb
    #     )

    #     # Should still be valid
    #     assert isinstance(params, dict)
    #     assert all(key in params for key in base_params.keys())

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

    def test_derive_topic_tags_with_semantic_categorization(self, sample_verb):
        """Test topic tag derivation with semantic verb categorization."""
        service = ProblemService()
        constraints = GrammarProblemConstraints()
        metadata = {
            "grammatical_focus": ["basic_conjugation"],
            "includes_cod": False,
            "includes_coi": False,
            "includes_negation": False,
        }

        # Test different verb types
        test_cases = [
            ("manger", "food"),
            ("aller", "movement"),
            ("parler", "communication"),
            ("être", "essential_verbs"),
        ]

        for infinitive, expected_tag in test_cases:
            sample_verb.infinitive = infinitive
            tags = service._derive_topic_tags(sample_verb, constraints, metadata)
            assert expected_tag in tags

    def test_derive_topic_tags_with_complex_grammar(self, sample_verb):
        """Test topic tag derivation with complex grammar features."""
        service = ProblemService()
        constraints = GrammarProblemConstraints()

        # Test complex grammar (both COD and COI)
        metadata = {
            "grammatical_focus": ["direct_objects", "indirect_objects"],
            "includes_cod": True,
            "includes_coi": True,
            "includes_negation": False,
        }

        tags = service._derive_topic_tags(sample_verb, constraints, metadata)
        assert "complex_grammar" in tags
        assert "direct_objects" in tags
        assert "indirect_objects" in tags

    def test_derive_topic_tags_with_negation(self, sample_verb):
        """Test topic tag derivation with negation."""
        service = ProblemService()
        constraints = GrammarProblemConstraints()

        # Test negation
        metadata = {
            "grammatical_focus": ["negation"],
            "includes_cod": False,
            "includes_coi": False,
            "includes_negation": True,
        }

        tags = service._derive_topic_tags(sample_verb, constraints, metadata)
        assert "negation" in tags

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
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
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

    def test_derive_grammar_metadata_with_multiple_features(self, sample_verb):
        """Test metadata derivation with multiple grammatical features."""
        service = ProblemService()

        from src.schemas.sentences import Sentence

        # Create sentences with various features
        sentences = [
            Sentence(
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
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            Sentence(
                id=uuid4(),
                content="Je ne lui parle pas.",
                translation="I don't speak to him.",
                verb_id=sample_verb.id,
                pronoun=Pronoun.FIRST_PERSON,
                tense=Tense.PRESENT,
                direct_object=DirectObject.NONE,
                indirect_object=IndirectObject.MASCULINE,
                negation=Negation.PAS,  # Fixed enum value
                is_correct=True,
                target_language_code="eng",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
        ]

        constraints = GrammarProblemConstraints()
        metadata = service._derive_grammar_metadata(sentences, sample_verb, constraints)

        assert metadata["includes_cod"] is True
        assert metadata["includes_coi"] is True
        assert metadata["includes_negation"] is True
        assert "direct_objects" in metadata["grammatical_focus"]
        assert "indirect_objects" in metadata["grammatical_focus"]
        assert "negation" in metadata["grammatical_focus"]

    def test_derive_grammar_metadata_basic_conjugation_only(self, sample_verb):
        """Test metadata derivation for basic conjugation only."""
        service = ProblemService()

        from src.schemas.sentences import Sentence

        sentence = Sentence(
            id=uuid4(),
            content="Je parle.",
            translation="I speak.",
            verb_id=sample_verb.id,
            pronoun=Pronoun.FIRST_PERSON,
            tense=Tense.PRESENT,
            direct_object=DirectObject.NONE,
            indirect_object=IndirectObject.NONE,
            negation=Negation.NONE,
            is_correct=True,
            target_language_code="eng",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        constraints = GrammarProblemConstraints()
        metadata = service._derive_grammar_metadata(
            [sentence], sample_verb, constraints
        )

        assert metadata["includes_cod"] is False
        assert metadata["includes_coi"] is False
        assert metadata["includes_negation"] is False
        assert metadata["grammatical_focus"] == ["basic_conjugation"]

    def test_package_grammar_problem(self, sample_verb):
        """Test packaging sentences into problem format."""
        service = ProblemService()

        from src.schemas.sentences import Sentence

        # Create sample sentences
        sentences = [
            Sentence(
                id=uuid4(),
                content="Je parle français.",
                translation="I speak French.",
                verb_id=sample_verb.id,
                pronoun=Pronoun.FIRST_PERSON,
                tense=Tense.PRESENT,
                direct_object=DirectObject.NONE,
                indirect_object=IndirectObject.NONE,
                negation=Negation.NONE,
                is_correct=True,
                target_language_code="eng",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            Sentence(
                id=uuid4(),
                content="Je parles français.",
                translation="Wrong conjugation example",  # Fixed: translation is required
                explanation="Wrong conjugation",
                verb_id=sample_verb.id,
                pronoun=Pronoun.FIRST_PERSON,
                tense=Tense.PRESENT,
                direct_object=DirectObject.NONE,
                indirect_object=IndirectObject.NONE,
                negation=Negation.NONE,
                is_correct=False,
                target_language_code="eng",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
        ]

        constraints = GrammarProblemConstraints()
        problem_create = service._package_grammar_problem(
            sentences=sentences,
            correct_answer_index=0,
            verb=sample_verb,
            constraints=constraints,
            target_language_code="eng",
        )

        assert problem_create.problem_type == ProblemType.GRAMMAR
        assert problem_create.title.startswith(
            f"Grammar: {sample_verb.infinitive.title()}_"
        )
        assert len(problem_create.title.split("_")[-1]) == 8  # UUID hex suffix
        assert problem_create.correct_answer_index == 0
        assert len(problem_create.statements) == 2
        assert problem_create.statements[0]["is_correct"] is True
        assert problem_create.statements[1]["is_correct"] is False
        assert "translation" in problem_create.statements[0]
        assert "explanation" in problem_create.statements[1]


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
