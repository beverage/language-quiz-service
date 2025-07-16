"""Problems service for business logic."""

import asyncio
import logging
import random
from typing import Any
from uuid import UUID, uuid4

from src.repositories.problem_repository import ProblemRepository
from src.schemas.problems import (
    GrammarProblemConstraints,
    Problem,
    ProblemCreate,
    ProblemFilters,
    ProblemSummary,
    ProblemType,
    ProblemUpdate,
)
from src.schemas.sentences import (
    DirectObject,
    IndirectObject,
    Negation,
    Pronoun,
    Sentence,
    Tense,
)
from src.services.sentence_service import SentenceService
from src.services.verb_service import VerbService

logger = logging.getLogger(__name__)


class ProblemService:
    """Service for problem business logic and orchestration."""

    def __init__(
        self,
        problem_repository: ProblemRepository | None = None,
        sentence_service: SentenceService | None = None,
        verb_service: VerbService | None = None,
    ):
        """Initialize the problems service with injectable dependencies."""
        self.problem_repository = problem_repository
        self.sentence_service = sentence_service or SentenceService()
        self.verb_service = verb_service or VerbService()

    async def _get_problem_repository(self) -> ProblemRepository:
        """Asynchronously get the problems repository, creating it if it doesn't exist."""
        if self.problem_repository is None:
            self.problem_repository = await ProblemRepository.create()
        return self.problem_repository

    async def create_problem(self, problem_data: ProblemCreate) -> Problem:
        """Create a new problem."""
        repo = await self._get_problem_repository()
        return await repo.create_problem(problem_data)

    async def get_problem(self, problem_id: UUID) -> Problem | None:
        """Get a problem by ID."""
        repo = await self._get_problem_repository()
        return await repo.get_problem(problem_id)

    async def get_problems(
        self, filters: ProblemFilters, include_statements: bool = True
    ) -> tuple[list[Problem], int]:
        """Get problems with filtering and pagination."""
        repo = await self._get_problem_repository()
        return await repo.get_problems(filters, include_statements)

    async def get_problem_summaries(
        self, filters: ProblemFilters
    ) -> tuple[list[ProblemSummary], int]:
        """Get lightweight problem summaries for list views."""
        repo = await self._get_problem_repository()
        return await repo.get_problem_summaries(filters)

    async def update_problem(
        self, problem_id: UUID, problem_data: ProblemUpdate
    ) -> Problem | None:
        """Update a problem."""
        repo = await self._get_problem_repository()
        return await repo.update_problem(problem_id, problem_data)

    async def delete_problem(self, problem_id: UUID) -> bool:
        """Delete a problem."""
        repo = await self._get_problem_repository()
        return await repo.delete_problem(problem_id)

    async def create_random_grammar_problem(
        self,
        constraints: GrammarProblemConstraints | None = None,
        statement_count: int = 4,
        target_language_code: str = "eng",
    ) -> Problem:
        """
        Create a random grammar problem by orchestrating sentence generation.

        This is the main integration point with your existing sentence generation system.
        """
        logger.info(
            f"🎯 Creating random grammar problem with {statement_count} statements"
        )

        # Apply default constraints if none provided
        if constraints is None:
            constraints = GrammarProblemConstraints()

        # Step 1: Select a random verb for consistency across statements
        verb = await self.verb_service.get_random_verb()
        if not verb:
            raise ValueError("No verbs available for problem generation")

        logger.info(f"📝 Selected verb: {verb.infinitive}")

        # Step 2: Generate random grammatical parameters
        grammatical_params = self._generate_grammatical_parameters(verb, constraints)

        # Step 3: Generate statements using your existing sentence system (in parallel)
        correct_answer_index = random.randint(0, statement_count - 1)

        # Prepare all sentence generation tasks
        sentence_tasks = []
        for i in range(statement_count):
            is_correct = i == correct_answer_index

            # Generate sentence with variations for incorrect answers
            sentence_params = self._vary_parameters_for_statement(
                grammatical_params, i, is_correct, verb
            )

            logger.info(
                f"🔄 Preparing statement {i+1}/{statement_count} "
                f"{'(correct)' if is_correct else '(incorrect)'}"
            )

            # Create task but don't await yet
            task = self.sentence_service.generate_sentence(
                verb_id=verb.id,
                **sentence_params,
                is_correct=is_correct,
                target_language_code=target_language_code,
            )
            sentence_tasks.append(task)

        # Execute all sentence generation in parallel
        logger.info(f"⚡ Generating {statement_count} statements in parallel...")
        sentences = await asyncio.gather(*sentence_tasks)

        # Find the actual correct answer index based on sentence service results
        actual_correct_index = None
        for i, sentence in enumerate(sentences):
            if sentence.is_correct:
                actual_correct_index = i
                break

        if actual_correct_index is None:
            raise ValueError(
                "No correct sentence was generated by the sentence service"
            )

        logger.info(f"🎯 Correct answer is at index {actual_correct_index}")

        # Step 4: Package into atomic problem format
        problem_data = self._package_grammar_problem(
            sentences=sentences,
            correct_answer_index=actual_correct_index,
            verb=verb,
            constraints=constraints,
            target_language_code=target_language_code,
        )

        # Step 5: Create and return the problem
        repo = await self._get_problem_repository()
        created_problem = await repo.create_problem(problem_data)

        logger.info(f"✅ Created grammar problem {created_problem.id}")
        return created_problem

    def _generate_grammatical_parameters(
        self, verb, constraints: GrammarProblemConstraints
    ) -> dict[str, Any]:
        """Generate base grammatical parameters for the problem."""
        # Use constraints if provided, otherwise randomize
        pronoun = random.choice(list(Pronoun))

        # Respect tense constraints or randomize
        if constraints.tenses_used:
            available_tenses = [
                Tense(t) for t in constraints.tenses_used if t != "imperatif"
            ]
        else:
            available_tenses = [t for t in Tense if t != Tense.IMPERATIF]

        tense = random.choice(available_tenses)

        # Apply verb-specific constraints for COD/COI
        can_use_cod = verb.can_have_cod and (constraints.includes_cod is not False)
        can_use_coi = verb.can_have_coi and (constraints.includes_coi is not False)

        # Determine direct and indirect objects
        if can_use_cod and random.choice([True, False]):
            direct_object = random.choice(
                [d for d in DirectObject if d != DirectObject.NONE]
            )
        else:
            direct_object = DirectObject.NONE

        if (
            can_use_coi
            and direct_object == DirectObject.NONE
            and random.choice([True, False])
        ):
            indirect_object = random.choice(
                [i for i in IndirectObject if i != IndirectObject.NONE]
            )
        else:
            indirect_object = IndirectObject.NONE

        # Handle negation
        if constraints.includes_negation or (
            constraints.includes_negation is None
            and random.choice([True, False, False])
        ):  # 33% chance
            negation = random.choice([n for n in Negation if n != Negation.NONE])
        else:
            negation = Negation.NONE

        return {
            "pronoun": pronoun,
            "tense": tense,
            "direct_object": direct_object,
            "indirect_object": indirect_object,
            "negation": negation,
        }

    def _vary_parameters_for_statement(
        self,
        base_params: dict[str, Any],
        statement_index: int,
        is_correct: bool,
        verb,
    ) -> dict[str, Any]:
        """Create parameter variations for each statement."""
        params = base_params.copy()

        if is_correct:
            # Correct statement uses base parameters as-is
            return params

        # For incorrect statements, introduce targeted errors
        error_type = statement_index % 3  # Cycle through error types

        if error_type == 0 and params["direct_object"] != DirectObject.NONE:
            # Error: Wrong direct object type or incorrect indirect object usage
            if random.choice([True, False]):
                # Switch to indirect object incorrectly
                params["direct_object"] = DirectObject.NONE
                params["indirect_object"] = random.choice(
                    [i for i in IndirectObject if i != IndirectObject.NONE]
                )
            else:
                # Wrong direct object gender/number
                current = params["direct_object"]
                available = [
                    d for d in DirectObject if d != DirectObject.NONE and d != current
                ]
                if available:
                    params["direct_object"] = random.choice(available)

        elif error_type == 1 and params["indirect_object"] != IndirectObject.NONE:
            # Error: Wrong indirect object type or incorrect direct object usage
            if random.choice([True, False]):
                # Switch to direct object incorrectly
                params["indirect_object"] = IndirectObject.NONE
                params["direct_object"] = random.choice(
                    [d for d in DirectObject if d != DirectObject.NONE]
                )
            else:
                # Wrong indirect object gender/number
                current = params["indirect_object"]
                available = [
                    i
                    for i in IndirectObject
                    if i != IndirectObject.NONE and i != current
                ]
                if available:
                    params["indirect_object"] = random.choice(available)

        elif error_type == 2:
            # Error: Wrong negation or pronoun agreement
            if params["negation"] != Negation.NONE:
                # Wrong negation type
                current = params["negation"]
                available = [n for n in Negation if n != Negation.NONE and n != current]
                if available:
                    params["negation"] = random.choice(available)
            else:
                # Add incorrect negation
                params["negation"] = random.choice(
                    [n for n in Negation if n != Negation.NONE]
                )

        return params

    def _package_grammar_problem(
        self,
        sentences: list[Sentence],
        correct_answer_index: int,
        verb,
        constraints: GrammarProblemConstraints,
        target_language_code: str,
    ) -> ProblemCreate:
        """Package sentences into atomic problem format."""

        # Convert sentences to statement format
        statements = []
        for sentence in sentences:
            statement = {
                "content": sentence.content,
                "is_correct": sentence.is_correct,
            }

            if sentence.is_correct:
                statement["translation"] = sentence.translation
            else:
                statement["explanation"] = sentence.explanation or "Grammar error"

            statements.append(statement)

        # Derive searchable metadata from generation parameters
        metadata = self._derive_grammar_metadata(sentences, verb, constraints)

        # Generate topic tags
        topic_tags = self._derive_topic_tags(verb, constraints, metadata)

        # Create the problem
        return ProblemCreate(
            problem_type=ProblemType.GRAMMAR,
            title=f"Grammar: {verb.infinitive.title()}_{uuid4().hex[:8]}",
            instructions="Choose the correctly formed French sentence.",
            correct_answer_index=correct_answer_index,
            target_language_code=target_language_code,
            statements=statements,
            topic_tags=topic_tags,
            source_statement_ids=[s.id for s in sentences],
            metadata=metadata,
        )

    def _derive_grammar_metadata(
        self,
        sentences: list[Sentence],
        verb,
        constraints: GrammarProblemConstraints,
    ) -> dict[str, Any]:
        """Derive searchable metadata from sentence generation parameters."""

        # Analyze what grammatical features are present
        has_cod = any(s.direct_object != DirectObject.NONE for s in sentences)
        has_coi = any(s.indirect_object != IndirectObject.NONE for s in sentences)
        has_negation = any(s.negation != Negation.NONE for s in sentences)

        # Determine grammatical focus
        grammatical_focus = []
        if has_cod:
            grammatical_focus.append("direct_objects")
        if has_coi:
            grammatical_focus.append("indirect_objects")
        if has_negation:
            grammatical_focus.append("negation")
        if not grammatical_focus:
            grammatical_focus.append("basic_conjugation")

        # Collect unique tenses and pronouns used
        tenses_used = list(set(s.tense.value for s in sentences))
        pronouns_used = list(set(s.pronoun.value for s in sentences))

        return {
            "grammatical_focus": grammatical_focus,
            "verb_infinitives": [verb.infinitive],
            "source_verb_ids": [str(verb.id)],
            "tenses_used": tenses_used,
            "pronouns_used": pronouns_used,
            "includes_negation": has_negation,
            "includes_cod": has_cod,
            "includes_coi": has_coi,
            "estimated_time_minutes": 2,
            "learning_objective": f"Practice {', '.join(grammatical_focus)} with {verb.infinitive}",
            "verb_classification": verb.classification.value
            if verb.classification
            else None,
            "verb_auxiliary": verb.auxiliary.value if verb.auxiliary else None,
        }

    def _derive_topic_tags(
        self,
        verb,
        constraints: GrammarProblemConstraints,
        metadata: dict[str, Any],
    ) -> list[str]:
        """Derive topic tags for searchability."""
        tags = []

        # Add verb-based tags (could be enhanced with semantic categorization)
        verb_infinitive = verb.infinitive.lower()

        # Basic semantic categorization (could be expanded)
        if verb_infinitive in ["manger", "boire", "cuisiner", "dîner"]:
            tags.append("food")
        elif verb_infinitive in ["aller", "venir", "partir", "arriver"]:
            tags.append("movement")
        elif verb_infinitive in ["parler", "dire", "écouter", "entendre"]:
            tags.append("communication")
        elif verb_infinitive in ["être", "avoir", "devenir"]:
            tags.append("essential_verbs")

        # Add grammatical focus tags
        tags.extend(metadata["grammatical_focus"])

        # Add difficulty-based tags
        if metadata.get("includes_cod") and metadata.get("includes_coi"):
            tags.append("complex_grammar")
        elif metadata.get("includes_negation"):
            tags.append("negation")
        else:
            tags.append("basic_grammar")

        return list(set(tags))  # Remove duplicates

    # Analytics and search methods
    async def get_problems_by_topic(
        self, topic_tags: list[str], limit: int = 50
    ) -> list[Problem]:
        """Get problems by topic tags."""
        repo = await self._get_problem_repository()
        return await repo.get_problems_by_topic_tags(topic_tags, limit)

    async def get_problems_using_verb(
        self, verb_id: UUID, limit: int = 50
    ) -> list[Problem]:
        """Get problems that use a specific verb."""
        repo = await self._get_problem_repository()
        metadata_query = {"source_verb_ids": [str(verb_id)]}
        return await repo.search_problems_by_metadata(metadata_query, limit)

    async def get_problems_by_grammatical_focus(
        self, focus: str, limit: int = 50
    ) -> list[Problem]:
        """Get problems focusing on specific grammatical concepts."""
        repo = await self._get_problem_repository()
        metadata_query = {"grammatical_focus": [focus]}
        return await repo.search_problems_by_metadata(metadata_query, limit)

    async def get_random_problem(
        self,
        problem_type: ProblemType | None = None,
        topic_tags: list[str] | None = None,
    ) -> Problem | None:
        """Get a random problem with optional filters."""
        repo = await self._get_problem_repository()
        return await repo.get_random_problem(problem_type, topic_tags)

    async def count_problems(
        self,
        problem_type: ProblemType | None = None,
        topic_tags: list[str] | None = None,
    ) -> int:
        """Count problems with optional filters."""
        repo = await self._get_problem_repository()
        return await repo.count_problems(problem_type, topic_tags)

    async def get_problem_statistics(self) -> dict[str, Any]:
        """Get problem statistics for analytics."""
        repo = await self._get_problem_repository()
        return await repo.get_problem_statistics()
