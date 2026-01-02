"""Main orchestrator for sentence prompt building."""

import random

from src.prompts.sentences.auxiliary_error_prompt import build_wrong_auxiliary_prompt
from src.prompts.sentences.conjugation_error_prompt import (
    build_wrong_conjugation_prompt,
)
from src.prompts.sentences.correct_prompt import build_correct_sentence_prompt
from src.prompts.sentences.error_types import ErrorType
from src.schemas.sentences import SentenceBase
from src.schemas.verbs import Tense, Verb


class SentencePromptBuilder:
    """Orchestrator for building sentence generation prompts."""

    def __init__(self):
        pass

    def select_error_types(
        self, sentence: SentenceBase, verb: Verb, count: int = 3
    ) -> list[ErrorType]:
        """Select appropriate error types for this sentence/verb combination.

        Args:
            sentence: The sentence configuration
            verb: The verb being used
            count: Number of error types to select (default 3)

        Returns:
            List of selected error types
        """
        available_errors = []

        # Wrong conjugation: always available (forms guaranteed distinct by helper)
        available_errors.append(ErrorType.WRONG_CONJUGATION)

        # Wrong auxiliary: only for compound tenses
        if sentence.tense in [Tense.PASSE_COMPOSE]:
            available_errors.append(ErrorType.WRONG_AUXILIARY)

        # If we need more errors than available, just use what we have
        if count > len(available_errors):
            count = len(available_errors)

        # Randomly select from available pool
        selected_errors = random.sample(available_errors, count)

        return selected_errors

    def build_prompt(
        self,
        sentence: SentenceBase,
        verb: Verb,
        conjugations: list,
        error_type: ErrorType | None = None,
    ) -> str:
        """Build the appropriate prompt based on sentence correctness and error type.

        Args:
            sentence: The sentence configuration
            verb: The verb being used
            conjugations: List of conjugation objects for the verb
            error_type: If sentence is incorrect, which error type to inject

        Returns:
            The complete prompt string
        """
        if not conjugations:
            raise ValueError(f"No conjugations provided for verb {verb.infinitive}")

        if sentence.is_correct:
            return build_correct_sentence_prompt(sentence, verb, conjugations)

        # For incorrect sentences, error_type must be provided
        if error_type is None:
            raise ValueError("error_type must be provided for incorrect sentences")

        # Route to appropriate error prompt builder
        if error_type == ErrorType.WRONG_CONJUGATION:
            return build_wrong_conjugation_prompt(sentence, verb, conjugations)
        elif error_type == ErrorType.WRONG_AUXILIARY:
            return build_wrong_auxiliary_prompt(sentence, verb, conjugations)
        else:
            raise ValueError(f"Unknown or unsupported error type: {error_type}")
