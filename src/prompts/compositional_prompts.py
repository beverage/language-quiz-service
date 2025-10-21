"""Compositional sentence generation system with targeted error injection."""

import random
from enum import Enum

from src.schemas.sentences import (
    Negation,
    Pronoun,
    SentenceBase,
)
from src.schemas.verbs import AuxiliaryType, Tense, Verb


class ErrorType(str, Enum):
    """Types of grammatical errors for incorrect sentences."""

    COD_PRONOUN_ERROR = "cod_pronoun_error"
    COI_PRONOUN_ERROR = "coi_pronoun_error"
    WRONG_CONJUGATION = "wrong_conjugation"
    WRONG_AUXILIARY = "wrong_auxiliary"
    PAST_PARTICIPLE_AGREEMENT = "past_participle_agreement"


class CompositionalPromptBuilder:
    """Builds specialized prompts for correct and incorrect sentence generation."""

    def __init__(self):
        pass

    def _get_pronoun_display(self, pronoun: str) -> str:
        """Convert pronoun enum to French display format."""
        pronoun_map = {
            "first_person": "je",
            "second_person": "tu",
            "third_person": "il/elle",
            "first_person_plural": "nous",
            "second_person_plural": "vous",
            "third_person_plural": "ils/elles",
        }
        return pronoun_map.get(pronoun, pronoun)

    def _build_base_template(
        self, sentence: SentenceBase, verb: Verb, for_correct: bool = True
    ) -> str:
        """Build the base template shared by all prompts."""
        pronoun_display = self._get_pronoun_display(sentence.pronoun.value)

        # Build negation display
        negation_display = (
            sentence.negation.value if sentence.negation != Negation.NONE else "none"
        )

        base = f"""You are a French grammar expert. Generate a creative, natural-sounding French sentence.

VERB DETAILS:
- Infinitive: {verb.infinitive}
- Translation: {verb.translation}
- Past Participle: {verb.past_participle}
- Auxiliary: {verb.auxiliary.value} (avoir/être)
- Reflexive: {verb.reflexive}
- Can have COD: {verb.can_have_cod}
- Can have COI: {verb.can_have_coi}

REQUIRED PARAMETERS:
- Pronoun: {pronoun_display}
- Tense: {sentence.tense.value}
- Negation: {negation_display}
- Direct Object (COD): {sentence.direct_object.value}
- Indirect Object (COI): {sentence.indirect_object.value}
"""

        if not for_correct:
            # For incorrect sentences, emphasize which features must be correct
            base += """
IMPORTANT: Unless the error instruction below specifically targets one of these features,
the negation, pronoun, and tense usage must be grammatically CORRECT.
"""

        return base

    def _build_creativity_section(self) -> str:
        """Build the creativity requirements section."""
        return """
CREATIVITY REQUIREMENTS:
- Use varied vocabulary and contexts
- Create realistic, interesting scenarios
- Vary sentence complexity when appropriate
- Include complements/infinitives when the verb allows
- Avoid repetitive patterns
"""

    def _build_response_format(self, sentence: SentenceBase) -> str:
        """Build the JSON response format section."""
        return f"""
RESPONSE FORMAT (JSON):
{{
    "sentence": "The French sentence",
    "translation": "English translation in {sentence.target_language_code}",
    "explanation": "Explanation of error (empty string for correct sentences)",
    "negation": "none, pas, jamais, rien, personne, plus, aucun, aucune, or encore",
    "direct_object": "none, masculine, feminine, or plural",
    "indirect_object": "none, masculine, feminine, or plural",
    "has_compliment_object_direct": "true or false",
    "has_compliment_object_indirect": "true or false"
}}

Field Instructions:
- direct_object: Return the grammatical gender/number of the direct object or "none"
- indirect_object: Return the grammatical gender/number of the indirect object or "none"
- negation: Return ONLY negation words or "none" if no negation present
- has_compliment_object_direct: true if COD pronoun (le/la/les) is used before verb
- has_compliment_object_indirect: true if COI pronoun (lui/leur) is used before verb
- Do NOT put actual object words (like "un livre") in direct_object or indirect_object fields

Format Requirements:
- Check all elisions are correct (e.g., 'Je habite' -> 'J'habite')
- Check all capitalization is correct
- Return well-formed JSON with no trailing commas
- Do not include any other text or comments
"""

    def build_correct_sentence_prompt(self, sentence: SentenceBase, verb: Verb) -> str:
        """Build prompt for generating a grammatically correct sentence."""
        base = self._build_base_template(sentence, verb, for_correct=True)
        creativity = self._build_creativity_section()
        response_format = self._build_response_format(sentence)

        instructions = """
[SPECIFIC INSTRUCTIONS]
Generate a grammatically CORRECT sentence that:
1. Uses all required parameters exactly as specified
2. Follows all French grammar rules:
   - Correct auxiliary verb (avoir/être)
   - Proper past participle agreement with être
   - Correct reflexive pronoun placement if reflexive verb
   - Proper negation structure (ne...pas, ne...jamais, etc.)
   - Correct COD/COI pronoun placement and agreement
   - Proper prepositions for indirect objects
3. Is semantically meaningful and idiomatic
4. Sounds natural to native speakers

Return explanation as an empty string.
"""

        return base + instructions + creativity + response_format

    def build_cod_error_prompt(self, sentence: SentenceBase, verb: Verb) -> str:
        """Build prompt for COD pronoun error."""
        base = self._build_base_template(sentence, verb, for_correct=False)
        creativity = self._build_creativity_section()
        response_format = self._build_response_format(sentence)

        instructions = f"""
[SPECIFIC INSTRUCTIONS]
Generate a sentence with an INCORRECT direct object pronoun (le/la/les).

DELIBERATE ERROR: The sentence must include a direct object pronoun that is WRONG.

STEP 1: Create a context requiring a {sentence.direct_object.value} direct object
STEP 2: Use the WRONG pronoun (le/la/les) - not the one matching the gender/number

Wrong pronoun strategies:
- If object should be masculine (le): use "la" or "les" instead
- If object should be feminine (la): use "le" or "les" instead
- If object should be plural (les): use "le" or "la" instead

Example:
- Context requires masculine object (le livre)
- Correct: "Je le vois" (I see it - masculine)
- INCORRECT: "Je la vois" (using feminine pronoun) ← Generate this type

Your sentence MUST contain the wrong direct object pronoun (le/la/les) before the verb.

Follow all other grammar rules correctly (conjugation, auxiliary, agreement, negation, etc.).
Only the direct object pronoun should be wrong.

Return explanation: State which wrong pronoun you used and what it should be.
Format: "The direct object pronoun should be '[correct]' not '[wrong one you used]'."
"""

        return base + instructions + creativity + response_format

    def build_coi_error_prompt(self, sentence: SentenceBase, verb: Verb) -> str:
        """Build prompt for COI pronoun error."""
        base = self._build_base_template(sentence, verb, for_correct=False)
        creativity = self._build_creativity_section()
        response_format = self._build_response_format(sentence)

        instructions = f"""
[SPECIFIC INSTRUCTIONS]
Generate a sentence with an INCORRECT indirect object pronoun (lui/leur).

DELIBERATE ERROR: The sentence must include an indirect object pronoun that is WRONG.

STEP 1: Create a context requiring a {sentence.indirect_object.value} indirect object
STEP 2: Use the WRONG pronoun (lui/leur) - opposite of what the context requires

Wrong pronoun strategies:
- If object should be singular (lui): use "leur" (plural) instead
- If object should be plural (leur): use "lui" (singular) instead

Example:
- Context requires plural indirect object (talking to multiple people)
- Correct: "Je leur parle" (I talk to them - plural)
- INCORRECT: "Je lui parle" (using singular pronoun) ← Generate this type

Your sentence MUST contain the wrong indirect object pronoun (lui/leur) before the verb.

Follow all other grammar rules correctly (conjugation, auxiliary, agreement, negation, etc.).
Only the indirect object pronoun should be wrong.

Return explanation: State which wrong pronoun you used and what it should be.
Format: "The indirect object pronoun should be '[correct]' not '[wrong one you used]'."
"""

        return base + instructions + creativity + response_format

    def build_wrong_conjugation_prompt(
        self, sentence: SentenceBase, verb: Verb, correct_conjugation: str | None = None
    ) -> str:
        """Build prompt for wrong verb conjugation error.

        Args:
            sentence: The sentence configuration
            verb: The verb being used
            correct_conjugation: The correct conjugation form from database (if known)
        """
        base = self._build_base_template(sentence, verb, for_correct=False)
        creativity = self._build_creativity_section()
        response_format = self._build_response_format(sentence)

        pronoun_display = self._get_pronoun_display(sentence.pronoun.value)

        # Build the correct form section
        correct_form_info = ""
        if correct_conjugation:
            correct_form_info = f"""
*** CRITICAL CONSTRAINT ***
FORBIDDEN FORM: "{correct_conjugation}"

The correct conjugation for {pronoun_display} is "{correct_conjugation}".
You are ABSOLUTELY FORBIDDEN from using the word "{correct_conjugation}" in your sentence.
You MUST use a DIFFERENT word - a different spelling entirely.

The wrong form you choose MUST:
1. Be spelled DIFFERENTLY than "{correct_conjugation}"
2. Not be letter-for-letter identical to "{correct_conjugation}"
3. Be a recognizably different word when you read it

VERIFICATION CHECKLIST:
[ ] Does my sentence contain the exact word "{correct_conjugation}"?
[ ] If YES -> I have FAILED. Start over with a different conjugation.
[ ] If NO -> Proceed.
***************************
"""

        instructions = f"""
[SPECIFIC INSTRUCTIONS]
*** CRITICAL: You MUST generate a sentence with an INCORRECT verb conjugation. ***
{correct_form_info}
DELIBERATE ERROR REQUIRED:
The verb "{verb.infinitive}" must be conjugated WRONG for "{pronoun_display}" in {sentence.tense.value}.

PROCESS:
1. First, identify the CORRECT conjugation:
   - Pronoun: {pronoun_display}
   - Verb: {verb.infinitive}
   - Tense: {sentence.tense.value}
   - Correct form: {correct_conjugation if correct_conjugation else '[determine this]'}"

2. Then, choose a DIFFERENT conjugation to use instead:

   STRATEGIES FOR WRONG CONJUGATION:
   - Use wrong person ending (je/tu/il forms are often different)
   - Use infinitive form: "{verb.infinitive}" instead of conjugated
   - Use wrong person's conjugation from the SAME tense
   - Drop or add letters incorrectly

   Example for "parler" + "tu" + "present":
   CORRECT: "Tu parles"
   WRONG OPTIONS: "Tu parle" (3rd person), "Tu parler" (infinitive), "Tu parlent" (3rd plural)

3. Build your sentence using the WRONG form you chose in step 2.

*** VERIFICATION BEFORE SUBMITTING ***
Confirm:
- Does your sentence contain the WRONG conjugation?
- Is the wrong form actually different from the correct form?
- Can you clearly identify which wrong form you used?

IF YOU ACCIDENTALLY USE THE CORRECT CONJUGATION, START OVER.

All other grammar must be correct (auxiliary, agreement, pronouns, negation, word order).
Only the verb conjugation of "{verb.infinitive}" should be wrong.

EXPLANATION FORMAT:
"The verb should be conjugated as '[correct form you identified in step 1]' for '{pronoun_display}', not '[wrong form you used in step 2]' because [reason why the wrong form is incorrect]."

Example explanation: "The verb should be conjugated as 'parles' for 'tu', not 'parle'."
"""

        return base + instructions + creativity + response_format

    def build_wrong_auxiliary_prompt(self, sentence: SentenceBase, verb: Verb) -> str:
        """Build prompt for wrong auxiliary verb error."""
        base = self._build_base_template(sentence, verb, for_correct=False)
        creativity = self._build_creativity_section()
        response_format = self._build_response_format(sentence)

        correct_auxiliary = verb.auxiliary.value
        wrong_auxiliary = "avoir" if verb.auxiliary == AuxiliaryType.ETRE else "être"

        instructions = f"""
[SPECIFIC INSTRUCTIONS]
Generate a sentence using the WRONG auxiliary verb for the compound tense.

DELIBERATE ERROR: The verb "{verb.infinitive}" requires auxiliary "{correct_auxiliary}"
in {sentence.tense.value}, but you must use "{wrong_auxiliary}" instead.

Example violations:
- Correct: "Je suis allé" (I went - aller uses être)
- INCORRECT: "J'ai allé" (using avoir instead) ← Generate this type of error

Follow all other grammar rules correctly (conjugation, agreement, pronouns, negation, etc.).
Only the auxiliary verb should be wrong.

Return explanation: A clear, concise sentence in English explaining which auxiliary
the verb requires. Do not use brackets or technical jargon.
"""

        return base + instructions + creativity + response_format

    def build_past_participle_agreement_prompt(
        self, sentence: SentenceBase, verb: Verb
    ) -> str:
        """Build prompt for past participle agreement error."""
        base = self._build_base_template(sentence, verb, for_correct=False)
        creativity = self._build_creativity_section()
        response_format = self._build_response_format(sentence)

        pronoun_display = self._get_pronoun_display(sentence.pronoun.value)

        instructions = f"""
[SPECIFIC INSTRUCTIONS]
Generate a sentence with INCORRECT past participle agreement.

DELIBERATE ERROR: When using auxiliary "être" in {sentence.tense.value}, the past
participle must agree with the subject "{pronoun_display}" in gender and number.
You must generate a sentence where this agreement is WRONG.

Determine what gender/number agreement is needed for "{pronoun_display}", then use
the WRONG form of the past participle.

Possible errors:
- Use masculine when feminine is needed
- Use singular when plural is needed
- Use no agreement when agreement is required

Example violations:
- Correct: "Elle est allée" (feminine agreement)
- INCORRECT: "Elle est allé" (masculine form) ← Generate this type of error

Follow all other grammar rules correctly (conjugation, auxiliary, pronouns, negation, etc.).
Only the past participle agreement should be wrong.

Return explanation: A clear, concise sentence in English explaining what the correct
past participle form should be. Do not use brackets or technical jargon.
"""

        return base + instructions + creativity + response_format

    def select_error_types(
        self, sentence: SentenceBase, verb: Verb, count: int = 3
    ) -> list[ErrorType]:
        """Select appropriate error types for this sentence/verb combination.

        Args:
            sentence: The sentence configuration
            verb: The verb being used
            count: Number of error types to select (default 3)

        Returns:
            List of selected error types (mandatory + random from available pool)
        """
        mandatory_errors = []
        available_errors = []

        # TODO: Temporarily disabled COD/COI errors until multi-clause sentences are implemented
        # These errors are ambiguous in single-clause sentences
        #
        # # Mandatory: COD error if direct object is present
        # if sentence.direct_object != DirectObject.NONE:
        #     mandatory_errors.append(ErrorType.COD_PRONOUN_ERROR)
        #
        # # Mandatory: COI error if indirect object is present
        # if sentence.indirect_object != IndirectObject.NONE:
        #     mandatory_errors.append(ErrorType.COI_PRONOUN_ERROR)

        # Available: Wrong conjugation (always applicable)
        # For now, only use conjugation errors until we implement multi-clause sentences
        available_errors.append(ErrorType.WRONG_CONJUGATION)

        # Available: Wrong auxiliary (only for compound tenses)
        if sentence.tense in [Tense.PASSE_COMPOSE]:
            available_errors.append(ErrorType.WRONG_AUXILIARY)

            # Available: Past participle agreement (only for être + compound tenses)
            # BUT: Only for pronouns with unambiguous gender (il/elle/ils/elles)
            # Exclude: je/tu/nous/vous (ambiguous - can be masculine or feminine)
            if verb.auxiliary == AuxiliaryType.ETRE:
                unambiguous_pronouns = [
                    Pronoun.THIRD_PERSON,  # il/elle
                    Pronoun.THIRD_PERSON_PLURAL,  # ils/elles
                ]
                if sentence.pronoun in unambiguous_pronouns:
                    available_errors.append(ErrorType.PAST_PARTICIPLE_AGREEMENT)

        # Calculate how many more errors we need
        remaining_count = count - len(mandatory_errors)

        # If we need more errors than available, just use what we have
        if remaining_count > len(available_errors):
            remaining_count = len(available_errors)

        # Randomly select from available pool
        selected_random = random.sample(available_errors, remaining_count)

        return mandatory_errors + selected_random

    def build_prompt(
        self,
        sentence: SentenceBase,
        verb: Verb,
        error_type: ErrorType | None = None,
        correct_conjugation: str | None = None,
    ) -> str:
        """Build the appropriate prompt based on sentence correctness and error type.

        Args:
            sentence: The sentence configuration
            verb: The verb being used
            error_type: If sentence is incorrect, which error type to inject
            correct_conjugation: The correct conjugation form from database (if available)

        Returns:
            The complete prompt string
        """
        if sentence.is_correct:
            return self.build_correct_sentence_prompt(sentence, verb)

        # For incorrect sentences, error_type must be provided
        if error_type is None:
            raise ValueError("error_type must be provided for incorrect sentences")

        # Route to appropriate error prompt builder
        if error_type == ErrorType.COD_PRONOUN_ERROR:
            return self.build_cod_error_prompt(sentence, verb)
        elif error_type == ErrorType.COI_PRONOUN_ERROR:
            return self.build_coi_error_prompt(sentence, verb)
        elif error_type == ErrorType.WRONG_CONJUGATION:
            return self.build_wrong_conjugation_prompt(
                sentence, verb, correct_conjugation
            )
        elif error_type == ErrorType.WRONG_AUXILIARY:
            return self.build_wrong_auxiliary_prompt(sentence, verb)
        elif error_type == ErrorType.PAST_PARTICIPLE_AGREEMENT:
            return self.build_past_participle_agreement_prompt(sentence, verb)
        else:
            raise ValueError(f"Unknown error type: {error_type}")
