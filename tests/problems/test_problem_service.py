"""Unit tests for the ProblemService."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
from uuid import uuid4

from src.services.problem_service import ProblemService
from src.repositories.problem_repository import ProblemRepository
from src.services.sentence_service import SentenceService
from src.services.verb_service import VerbService
from src.schemas.problems import (
    Problem,
    ProblemCreate,
    ProblemUpdate,
    ProblemType,
    ProblemFilters,
    ProblemSummary,
    GrammarProblemConstraints,
)
from src.schemas.sentences import (
    Sentence,
    Pronoun,
    Tense,
    DirectObject,
    IndirectObject,
    Negation,
)
from src.schemas.verbs import Verb, AuxiliaryType, VerbClassification


@pytest.fixture
def mock_problem_repository():
    """Mock ProblemRepository for testing."""
    return AsyncMock(spec=ProblemRepository)


@pytest.fixture
def mock_sentence_service():
    """Mock SentenceService for testing."""
    return AsyncMock(spec=SentenceService)


@pytest.fixture
def mock_verb_service():
    """Mock VerbService for testing."""
    return AsyncMock(spec=VerbService)


@pytest.fixture
def sample_verb():
    """Sample verb for testing."""
    return Verb(
        id=uuid4(),
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
        can_have_coi=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_sentence():
    """Sample sentence for testing."""
    return Sentence(
        id=uuid4(),
        content="Je parle français.",
        translation="I speak French.",
        verb_id=uuid4(),
        pronoun=Pronoun.FIRST_PERSON,
        tense=Tense.PRESENT,
        direct_object=DirectObject.NONE,
        indirect_object=IndirectObject.NONE,
        negation=Negation.NONE,
        is_correct=True,
        target_language_code="eng",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_problem():
    """Sample problem for testing."""
    return Problem(
        id=uuid4(),
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
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def problem_service(mock_problem_repository, mock_sentence_service, mock_verb_service):
    """ProblemService instance with mocked dependencies."""
    return ProblemService(
        problem_repository=mock_problem_repository,
        sentence_service=mock_sentence_service,
        verb_service=mock_verb_service,
    )


@pytest.fixture
def problem_service_no_deps():
    """ProblemService instance without injected dependencies."""
    return ProblemService()


@pytest.mark.unit
class TestProblemServiceInitialization:
    """Test cases for ProblemService initialization."""

    def test_init_with_dependencies(
        self, mock_problem_repository, mock_sentence_service, mock_verb_service
    ):
        """Test initialization with injected dependencies."""
        service = ProblemService(
            problem_repository=mock_problem_repository,
            sentence_service=mock_sentence_service,
            verb_service=mock_verb_service,
        )

        assert service.problem_repository == mock_problem_repository
        assert service.sentence_service == mock_sentence_service
        assert service.verb_service == mock_verb_service

    def test_init_without_dependencies(self):
        """Test initialization without injected dependencies."""
        service = ProblemService()

        assert service.problem_repository is None
        assert isinstance(service.sentence_service, SentenceService)
        assert isinstance(service.verb_service, VerbService)

    @pytest.mark.asyncio
    @patch("src.services.problem_service.ProblemRepository.create")
    async def test_get_problem_repository_lazy_init(self, mock_create):
        """Test lazy initialization of problems repository."""
        mock_repo = AsyncMock()
        mock_create.return_value = mock_repo

        service = ProblemService()
        repo = await service._get_problem_repository()

        assert repo == mock_repo
        assert service.problem_repository == mock_repo
        mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_problem_repository_existing(
        self, problem_service, mock_problem_repository
    ):
        """Test getting existing problems repository."""
        repo = await problem_service._get_problem_repository()

        assert repo == mock_problem_repository


@pytest.mark.unit
@pytest.mark.asyncio
class TestProblemServiceCRUD:
    """Test cases for basic CRUD operations."""

    async def test_create_problem(
        self, problem_service, mock_problem_repository, sample_problem
    ):
        """Test creating a problem."""
        problem_data = ProblemCreate(**sample_problem.model_dump())
        mock_problem_repository.create_problem.return_value = sample_problem

        result = await problem_service.create_problem(problem_data)

        assert result == sample_problem
        mock_problem_repository.create_problem.assert_called_once_with(problem_data)

    async def test_get_problem(
        self, problem_service, mock_problem_repository, sample_problem
    ):
        """Test getting a problem by ID."""
        problem_id = sample_problem.id
        mock_problem_repository.get_problem.return_value = sample_problem

        result = await problem_service.get_problem(problem_id)

        assert result == sample_problem
        mock_problem_repository.get_problem.assert_called_once_with(problem_id)

    async def test_get_problems(
        self, problem_service, mock_problem_repository, sample_problem
    ):
        """Test getting problems with filters."""
        filters = ProblemFilters(problem_type=ProblemType.GRAMMAR)
        mock_problem_repository.get_problems.return_value = ([sample_problem], 1)

        problems, total = await problem_service.get_problems(filters)

        assert problems == [sample_problem]
        assert total == 1
        mock_problem_repository.get_problems.assert_called_once_with(filters, True)

    async def test_get_problem_summaries(
        self, problem_service, mock_problem_repository
    ):
        """Test getting problem summaries."""
        filters = ProblemFilters()
        mock_summary = ProblemSummary(
            id=uuid4(),
            problem_type=ProblemType.GRAMMAR,
            title="Test",
            instructions="Test instructions",
            correct_answer_index=0,
            topic_tags=[],
            created_at=datetime.now(timezone.utc),
            statement_count=2,
        )
        mock_problem_repository.get_problem_summaries.return_value = ([mock_summary], 1)

        summaries, total = await problem_service.get_problem_summaries(filters)

        assert summaries == [mock_summary]
        assert total == 1
        mock_problem_repository.get_problem_summaries.assert_called_once_with(filters)

    async def test_update_problem(
        self, problem_service, mock_problem_repository, sample_problem
    ):
        """Test updating a problem."""
        problem_id = sample_problem.id
        update_data = ProblemUpdate(title="Updated Title")
        mock_problem_repository.update_problem.return_value = sample_problem

        result = await problem_service.update_problem(problem_id, update_data)

        assert result == sample_problem
        mock_problem_repository.update_problem.assert_called_once_with(
            problem_id, update_data
        )

    async def test_delete_problem(self, problem_service, mock_problem_repository):
        """Test deleting a problem."""
        problem_id = uuid4()
        mock_problem_repository.delete_problem.return_value = True

        result = await problem_service.delete_problem(problem_id)

        assert result is True
        mock_problem_repository.delete_problem.assert_called_once_with(problem_id)


@pytest.mark.unit
@pytest.mark.asyncio
class TestProblemServiceGrammarGeneration:
    """Test cases for grammar problem generation."""

    async def test_create_random_grammar_problem_success(
        self,
        problem_service,
        mock_problem_repository,
        mock_sentence_service,
        mock_verb_service,
        sample_verb,
        sample_sentence,
        sample_problem,
    ):
        """Test successful creation of random grammar problem."""
        # Mock verb service
        mock_verb_service.get_random_verb.return_value = sample_verb

        # Mock sentence service - create multiple sentences
        sentences = []
        for i in range(4):
            sentence = Sentence(
                id=uuid4(),
                content=f"Je parle français {i}.",
                translation="I speak French.",
                verb_id=sample_verb.id,
                pronoun=Pronoun.FIRST_PERSON,
                tense=Tense.PRESENT,
                direct_object=DirectObject.NONE,
                indirect_object=IndirectObject.NONE,
                negation=Negation.NONE,
                is_correct=(i == 0),  # First one is correct
                target_language_code="eng",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            sentences.append(sentence)

        mock_sentence_service.generate_sentence.side_effect = sentences

        # Mock repository
        mock_problem_repository.create_problem.return_value = sample_problem

        # Test with constraints
        constraints = GrammarProblemConstraints(
            grammatical_focus=["basic_conjugation"],
            includes_negation=False,
        )

        result = await problem_service.create_random_grammar_problem(
            constraints=constraints,
            statement_count=4,
            target_language_code="eng",
        )

        assert result == sample_problem
        mock_verb_service.get_random_verb.assert_called_once()
        assert mock_sentence_service.generate_sentence.call_count == 4
        mock_problem_repository.create_problem.assert_called_once()

    async def test_create_random_grammar_problem_no_verb(
        self,
        problem_service,
        mock_verb_service,
    ):
        """Test grammar problem creation when no verb is available."""
        mock_verb_service.get_random_verb.return_value = None

        with pytest.raises(
            ValueError, match="No verbs available for problem generation"
        ):
            await problem_service.create_random_grammar_problem()

    async def test_create_random_grammar_problem_default_constraints(
        self,
        problem_service,
        mock_problem_repository,
        mock_sentence_service,
        mock_verb_service,
        sample_verb,
        sample_problem,
    ):
        """Test grammar problem creation with default constraints."""
        mock_verb_service.get_random_verb.return_value = sample_verb

        # Create mock sentences
        sentences = [
            Sentence(
                id=uuid4(),
                content=f"Sentence {i}",
                translation="Translation",
                verb_id=sample_verb.id,
                pronoun=Pronoun.FIRST_PERSON,
                tense=Tense.PRESENT,
                direct_object=DirectObject.NONE,
                indirect_object=IndirectObject.NONE,
                negation=Negation.NONE,
                is_correct=(i == 0),
                target_language_code="eng",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            for i in range(4)
        ]
        mock_sentence_service.generate_sentence.side_effect = sentences
        mock_problem_repository.create_problem.return_value = sample_problem

        result = await problem_service.create_random_grammar_problem()

        assert result == sample_problem
        # Should use default constraints (None)
        mock_verb_service.get_random_verb.assert_called_once()


@pytest.mark.unit
class TestProblemServiceParameterGeneration:
    """Test cases for parameter generation methods."""

    def test_generate_grammatical_parameters_default(
        self, problem_service, sample_verb
    ):
        """Test generating grammatical parameters with default constraints."""
        constraints = GrammarProblemConstraints()

        params = problem_service._generate_grammatical_parameters(
            sample_verb, constraints
        )

        assert "pronoun" in params
        assert "tense" in params
        assert "direct_object" in params
        assert "indirect_object" in params
        assert "negation" in params
        assert isinstance(params["pronoun"], Pronoun)
        assert isinstance(params["tense"], Tense)
        assert params["tense"] != Tense.IMPERATIF  # Should exclude imperative

    def test_generate_grammatical_parameters_with_constraints(
        self, problem_service, sample_verb
    ):
        """Test generating parameters with specific constraints."""
        constraints = GrammarProblemConstraints(
            tenses_used=["present", "passe_compose"],
            includes_negation=True,
            includes_cod=True,
        )

        params = problem_service._generate_grammatical_parameters(
            sample_verb, constraints
        )

        assert params["tense"] in [Tense.PRESENT, Tense.PASSE_COMPOSE]
        assert params["negation"] != Negation.NONE  # Should include negation
        # Note: COD behavior depends on random choices and verb capabilities

    def test_vary_parameters_for_correct_statement(self, problem_service, sample_verb):
        """Test parameter variation for correct statements."""
        base_params = {
            "pronoun": Pronoun.FIRST_PERSON,
            "tense": Tense.PRESENT,
            "direct_object": DirectObject.MASCULINE,
            "indirect_object": IndirectObject.NONE,
            "negation": Negation.NONE,
        }

        params = problem_service._vary_parameters_for_statement(
            base_params, 0, True, sample_verb
        )

        # Correct statement should use base parameters unchanged
        assert params == base_params

    def test_vary_parameters_for_incorrect_statement(
        self, problem_service, sample_verb
    ):
        """Test parameter variation for incorrect statements."""
        base_params = {
            "pronoun": Pronoun.FIRST_PERSON,
            "tense": Tense.PRESENT,
            "direct_object": DirectObject.MASCULINE,
            "indirect_object": IndirectObject.NONE,
            "negation": Negation.NONE,
        }

        params = problem_service._vary_parameters_for_statement(
            base_params, 1, False, sample_verb
        )

        # Should introduce some variation for incorrect statement
        # The exact variation depends on the error type logic
        assert isinstance(params, dict)
        assert all(key in params for key in base_params.keys())

    def test_package_grammar_problem(self, problem_service, sample_verb):
        """Test packaging sentences into problem format."""
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
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
            Sentence(
                id=uuid4(),
                content="Je parles français.",
                translation="",
                verb_id=sample_verb.id,
                pronoun=Pronoun.FIRST_PERSON,
                tense=Tense.PRESENT,
                direct_object=DirectObject.NONE,
                indirect_object=IndirectObject.NONE,
                negation=Negation.NONE,
                is_correct=False,
                explanation="Wrong conjugation",
                target_language_code="eng",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
        ]

        constraints = GrammarProblemConstraints()
        correct_answer_index = 0

        problem_create = problem_service._package_grammar_problem(
            sentences, correct_answer_index, sample_verb, constraints, "eng"
        )

        assert isinstance(problem_create, ProblemCreate)
        assert problem_create.problem_type == ProblemType.GRAMMAR
        assert problem_create.title == "Grammar: Parler"
        assert problem_create.correct_answer_index == 0
        assert len(problem_create.statements) == 2
        assert problem_create.statements[0]["is_correct"] is True
        assert problem_create.statements[1]["is_correct"] is False
        assert "translation" in problem_create.statements[0]
        assert "explanation" in problem_create.statements[1]

    def test_derive_grammar_metadata(self, problem_service, sample_verb):
        """Test deriving metadata from sentences."""
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
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
        ]

        constraints = GrammarProblemConstraints()

        metadata = problem_service._derive_grammar_metadata(
            sentences, sample_verb, constraints
        )

        assert "grammatical_focus" in metadata
        assert "direct_objects" in metadata["grammatical_focus"]
        assert metadata["includes_cod"] is True
        assert metadata["includes_coi"] is False
        assert metadata["includes_negation"] is False
        assert "parler" in metadata["verb_infinitives"]

    @pytest.mark.parametrize(
        "verb_infinitive,expected_tag",
        [
            ("manger", "food"),
            ("aller", "movement"),
            ("parler", "communication"),
            ("être", "essential_verbs"),
            ("dormir", None),  # Should not match any category
        ],
    )
    def test_derive_topic_tags(self, problem_service, verb_infinitive, expected_tag):
        """Test deriving topic tags from verb and metadata."""
        verb = Verb(
            id=uuid4(),
            infinitive=verb_infinitive,
            auxiliary=AuxiliaryType.AVOIR,
            reflexive=False,
            target_language_code="eng",
            translation="test",
            past_participle="test",
            present_participle="test",
            classification=VerbClassification.FIRST_GROUP,
            is_irregular=False,
            can_have_cod=True,
            can_have_coi=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        constraints = GrammarProblemConstraints()
        metadata = {
            "grammatical_focus": ["basic_conjugation"],
            "includes_cod": False,
            "includes_coi": False,
            "includes_negation": False,
        }

        tags = problem_service._derive_topic_tags(verb, constraints, metadata)

        assert "basic_conjugation" in tags
        assert "basic_grammar" in tags
        if expected_tag:
            assert expected_tag in tags


@pytest.mark.unit
@pytest.mark.asyncio
class TestProblemServiceAnalytics:
    """Test cases for analytics and search methods."""

    async def test_get_problems_by_topic(
        self, problem_service, mock_problem_repository, sample_problem
    ):
        """Test getting problems by topic tags."""
        topic_tags = ["grammar", "basic_grammar"]
        mock_problem_repository.get_problems_by_topic_tags.return_value = [
            sample_problem
        ]

        result = await problem_service.get_problems_by_topic(topic_tags, 25)

        assert result == [sample_problem]
        mock_problem_repository.get_problems_by_topic_tags.assert_called_once_with(
            topic_tags, 25
        )

    async def test_get_problems_using_verb(
        self, problem_service, mock_problem_repository, sample_problem
    ):
        """Test getting problems using a specific verb."""
        verb_id = uuid4()
        mock_problem_repository.search_problems_by_metadata.return_value = [
            sample_problem
        ]

        result = await problem_service.get_problems_using_verb(verb_id, 25)

        assert result == [sample_problem]
        expected_query = {"source_verb_ids": [str(verb_id)]}
        mock_problem_repository.search_problems_by_metadata.assert_called_once_with(
            expected_query, 25
        )

    async def test_get_problems_by_grammatical_focus(
        self, problem_service, mock_problem_repository, sample_problem
    ):
        """Test getting problems by grammatical focus."""
        focus = "direct_objects"
        mock_problem_repository.search_problems_by_metadata.return_value = [
            sample_problem
        ]

        result = await problem_service.get_problems_by_grammatical_focus(focus, 25)

        assert result == [sample_problem]
        expected_query = {"grammatical_focus": [focus]}
        mock_problem_repository.search_problems_by_metadata.assert_called_once_with(
            expected_query, 25
        )

    async def test_get_random_problem(
        self, problem_service, mock_problem_repository, sample_problem
    ):
        """Test getting a random problem."""
        mock_problem_repository.get_random_problem.return_value = sample_problem

        result = await problem_service.get_random_problem(
            problem_type=ProblemType.GRAMMAR, topic_tags=["grammar"]
        )

        assert result == sample_problem
        mock_problem_repository.get_random_problem.assert_called_once_with(
            ProblemType.GRAMMAR, ["grammar"]
        )

    async def test_count_problems(self, problem_service, mock_problem_repository):
        """Test counting problems."""
        mock_problem_repository.count_problems.return_value = 42

        result = await problem_service.count_problems(
            problem_type=ProblemType.GRAMMAR, topic_tags=["grammar"]
        )

        assert result == 42
        mock_problem_repository.count_problems.assert_called_once_with(
            ProblemType.GRAMMAR, ["grammar"]
        )

    async def test_get_problem_statistics(
        self, problem_service, mock_problem_repository
    ):
        """Test getting problem statistics."""
        mock_stats = {
            "total_problems": 100,
            "problems_by_type": {"grammar": 80, "vocabulary": 20},
        }
        mock_problem_repository.get_problem_statistics.return_value = mock_stats

        result = await problem_service.get_problem_statistics()

        assert result == mock_stats
        mock_problem_repository.get_problem_statistics.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
class TestProblemServiceLazyInitialization:
    """Test cases for lazy initialization scenarios."""

    @patch("src.services.problem_service.ProblemRepository.create")
    async def test_crud_operations_with_lazy_init(self, mock_create, sample_problem):
        """Test that CRUD operations work with lazy repository initialization."""
        mock_repo = AsyncMock()
        mock_repo.get_problem.return_value = sample_problem
        mock_create.return_value = mock_repo

        service = ProblemService()  # No repository injected

        result = await service.get_problem(sample_problem.id)

        assert result == sample_problem
        mock_create.assert_called_once()
        mock_repo.get_problem.assert_called_once_with(sample_problem.id)

    @patch("src.services.problem_service.ProblemRepository.create")
    async def test_multiple_operations_reuse_repository(
        self, mock_create, sample_problem
    ):
        """Test that multiple operations reuse the same repository instance."""
        mock_repo = AsyncMock()
        mock_repo.get_problem.return_value = sample_problem
        mock_repo.count_problems.return_value = 5
        mock_create.return_value = mock_repo

        service = ProblemService()

        # First operation
        await service.get_problem(sample_problem.id)
        # Second operation
        await service.count_problems()

        # Repository should only be created once
        mock_create.assert_called_once()
        assert service.problem_repository == mock_repo
