"""Main orchestrator for sentence prompt building."""

import random

from src.prompts.sentences.auxiliary_error_prompt import build_wrong_auxiliary_prompt
from src.prompts.sentences.conjugation_error_prompt import (
    build_wrong_conjugation_prompt,
)
from src.prompts.sentences.correct_prompt import build_correct_sentence_prompt
from src.prompts.sentences.error_types import ErrorType
from src.prompts.sentences.pronoun_prompt import (
    build_correct_pronoun_prompt,
    build_pronoun_error_prompt,
)
from src.prompts.sentences.templates import COMPOUND_TENSES
from src.schemas.problems import GrammarFocus
from src.schemas.sentences import DirectObject, IndirectObject, SentenceBase
from src.schemas.verbs import Verb

# Error types by focus area
CONJUGATION_ERRORS = {ErrorType.WRONG_CONJUGATION, ErrorType.WRONG_AUXILIARY}
PRONOUN_ERRORS = {
    ErrorType.WRONG_PLACEMENT,
    ErrorType.WRONG_ORDER,
    ErrorType.WRONG_CATEGORY,
    ErrorType.WRONG_GENDER,
    ErrorType.WRONG_NUMBER,
}


class SentencePromptBuilder:
    """Orchestrator for building sentence generation prompts."""

    def __init__(self):
        pass

    def select_error_types(
        self,
        sentence: SentenceBase,
        verb: Verb,
        focus: GrammarFocus = GrammarFocus.CONJUGATION,
        count: int = 3,
    ) -> list[ErrorType]:
        """Select appropriate error types for this sentence/verb/focus combination.

        Args:
            sentence: The sentence configuration
            verb: The verb being used
            focus: The grammar focus area (conjugation or pronouns)
            count: Number of error types to select (default 3)

        Returns:
            List of selected error types
        """
        available_errors = []

        if focus == GrammarFocus.CONJUGATION:
            # Wrong conjugation: always available (forms guaranteed distinct by helper)
            available_errors.append(ErrorType.WRONG_CONJUGATION)

            # Wrong auxiliary: only for compound tenses
            if sentence.tense in COMPOUND_TENSES:
                available_errors.append(ErrorType.WRONG_AUXILIARY)

        elif focus == GrammarFocus.PRONOUNS:
            # Determine what the sentence actually has
            has_cod = sentence.direct_object not in (
                DirectObject.NONE,
                DirectObject.ANY,
            )
            has_coi = sentence.indirect_object not in (
                IndirectObject.NONE,
                IndirectObject.ANY,
            )

            # WRONG_PLACEMENT: valid for any pronoun (COD or COI)
            if has_cod or has_coi:
                available_errors.append(ErrorType.WRONG_PLACEMENT)

            # WRONG_ORDER: requires both COD and COI (double pronouns)
            if sentence.has_double_pronouns:
                available_errors.append(ErrorType.WRONG_ORDER)

            # WRONG_CATEGORY: tests COD↔COI confusion
            # Only valid for non-ditransitive verbs (verbs that take ONE type, not both)
            # Ditransitive verbs (can_have_cod AND can_have_coi) create incomplete sentences
            is_ditransitive = verb.can_have_cod and verb.can_have_coi
            if (has_cod or has_coi) and not is_ditransitive:
                available_errors.append(ErrorType.WRONG_CATEGORY)

            # WRONG_GENDER: only valid for COD (le vs la distinction)
            # COI has no gender distinction (lui for both masc/fem)
            # Also: compound tenses use avoir (ai/as/a/avons/avez/ont/avais/etc.)
            # which ALL start with vowels → le/la become l' → gender invisible!
            is_compound_tense = sentence.tense in COMPOUND_TENSES
            if has_cod and verb.can_have_cod and not is_compound_tense:
                available_errors.append(ErrorType.WRONG_GENDER)

            # WRONG_NUMBER: valid for both COD (le/la vs les) and COI (lui vs leur)
            if (has_cod and verb.can_have_cod) or (has_coi and verb.can_have_coi):
                available_errors.append(ErrorType.WRONG_NUMBER)

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
        focus: GrammarFocus = GrammarFocus.CONJUGATION,
    ) -> str:
        """Build the appropriate prompt based on sentence correctness and error type.

        Args:
            sentence: The sentence configuration
            verb: The verb being used
            conjugations: List of conjugation objects for the verb
            error_type: If sentence is incorrect, which error type to inject
            focus: The grammar focus area (conjugation or pronouns)

        Returns:
            The complete prompt string
        """
        if not conjugations:
            raise ValueError(f"No conjugations provided for verb {verb.infinitive}")

        if sentence.is_correct:
            # Route to correct prompt based on focus
            if focus == GrammarFocus.PRONOUNS:
                return build_correct_pronoun_prompt(sentence, verb, conjugations)
            return build_correct_sentence_prompt(sentence, verb, conjugations)

        # For incorrect sentences, error_type must be provided
        if error_type is None:
            raise ValueError("error_type must be provided for incorrect sentences")

        # Route to appropriate error prompt builder based on error type
        if error_type in CONJUGATION_ERRORS:
            if error_type == ErrorType.WRONG_CONJUGATION:
                return build_wrong_conjugation_prompt(sentence, verb, conjugations)
            elif error_type == ErrorType.WRONG_AUXILIARY:
                return build_wrong_auxiliary_prompt(sentence, verb, conjugations)

        elif error_type in PRONOUN_ERRORS:
            return build_pronoun_error_prompt(sentence, verb, conjugations, error_type)

        raise ValueError(f"Unknown or unsupported error type: {error_type}")
