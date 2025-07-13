from src.schemas.sentences import DirectObject, IndirectObject, Negation, Sentence
from src.schemas.verbs import Verb


class SentencePromptGenerator:
    """Generates prompts for the sentence of a given verb."""

    def __init__(self):
        pass

    def _get_sentence_prompt(self, sentence: Sentence, sentence_properties: str) -> str:
        return f"""
You are a French grammar expert.  Construct a sentence in French with the following properties:

{sentence_properties}

{{
    "sentence": "",
    "translation": "",
    "is_correct": "true or false",
    "explanation": "",
    "negation": {sentence.negation.value},
    "direct_object": {sentence.direct_object.value},
    "indirect_object": {sentence.indirect_object.value}
    "has_compliment_object_direct": "",
    "has_compliment_object_indirect": "",
}}

Rules:
- The sentence must semantically and idiomaticallymake sense.
- All prepositions match their indirect, or subordinate pronouns.
- If the sentence generated does not have a complement object direct - a le, la, or les before the verb - set has_compliment_object_direct to false.
- If the sentence generated does not have a complement object indirect - a lui, la, or leur before the verb - set has_compliment_object_indirect to false.
- If the verb requires additional objects or infinitives afterwards, add some.  They must agree in gender and number.
- If the conjugation uses the participle, and the auxiliary is 'être', make sure the number and gender match the subject.
- If verb is reflexive, use the reflexive pronoun in the sentence.
- If the sentence is not correct, provide a short explanation of why it is incorrect.

Format:
- Check all elisions are correct.  Examples: 'Je habite' -> 'J'habite', or 'Est-ce que il est là' -> 'Est-ce qu'il est là.'
- Check all capitalization is correct.
- Return the translation in {sentence.target_language_code}.
- Return well-formed JSON.  Do not include any other text or comments.  Do not include trailing commas.
"""

    def __sentence_properties(self, sentence: Sentence, verb: Verb) -> str:
        return f"""The sentence uses {sentence.pronoun.value} as the subject.
The sentence uses {sentence.tense.value} as the tense.
The sentence uses {verb.infinitive} as the verb.
The sentence uses {verb.auxiliary} as the auxiliary.
"""

    def __compliment_object_direct(self, sentence: Sentence, verb: Verb) -> str:
        return f"""
The sentance must contain a {sentence.direct_object.value} compliment direct object before the verb if the verb {verb.infinitive} allows it.
A compliment direct object is a direct object that is not the actual direct object, comes before the verb, and is either le, la, or les.  It
replaces the actual direct object.
    """

    def __compliment_object_indirect(self, sentence: Sentence, verb: Verb) -> str:
        return f"""
The sentence must contain an {sentence.indirect_object.value} compliment indirect object before the verb if the verb {verb.infinitive} allows it.
A compliment indirect object is an indirect object that is not the actual indirect object, comes before the verb, and is either lui, la, or leur.  It
replaces the actual indirect object.
    """

    def __negation(self, sentence):
        return f"""The sentence must contain the negation {sentence.negation.value}."""

    def __correctness(self, sentence: Sentence) -> str:
        if not sentence.is_correct:
            prompt = [
                """
The sentence will contain one or more grammatical errors.  These can include incorrect conjugation, number and 
gender disagreements, incorrect object agreement, incorrect pronoun agreement, incorrect auxiliary agreement, etc.
"""
            ]
            if sentence.direct_object != DirectObject.NONE:
                prompt.append("The complement object should be incorrect.")

            if sentence.indirect_object != IndirectObject.NONE:
                prompt.append("The indirect pronoun should be incorrect.")

            return "\n".join(prompt)
        else:
            return """The sentence will be grammatically correct."""

    def generate_sentence_prompt(self, sentence: Sentence, verb: Verb) -> str:
        sentence_properties = [self.__sentence_properties(sentence, verb)]

        if sentence.direct_object != DirectObject.NONE:
            sentence_properties.append(self.__compliment_object_direct(sentence, verb))

        if sentence.indirect_object != IndirectObject.NONE:
            sentence_properties.append(
                self.__compliment_object_indirect(sentence, verb)
            )

        if sentence.negation != Negation.NONE:
            sentence_properties.append(self.__negation(sentence))

        if not sentence.is_correct:
            sentence_properties.append(self.__correctness(sentence))

        return self._get_sentence_prompt(
            sentence, sentence_properties="\n".join(sentence_properties)
        )

    def generate_correctness_prompt(self, sentence: Sentence, verb: Verb) -> str:
        return f"""
You are a French grammar expert.  Review the following sentence, and if it is grammatical, idiomatical, and semantical correctness.

{sentence.content}

The sentence must have the following properties:
- The sentence uses {sentence.pronoun.value} as the subject.
- The sentence uses {sentence.tense.value} as the tense.
- The sentence uses {verb.infinitive} as the verb.
- The sentence uses {verb.auxiliary} as the auxiliary.

Return the return the result as json with the following fields:
- is_correct: true or false
- explanation: if the sentence is incorrect, a short explanation of why the sentence is incorrect
- actual_compliment_object_direct: none, masculine, feminine, or plural
- actual_compliment_object_indirect: none, masculine, feminine, or plural
- actual_negation: the actual negation of the object, or none
- direct_object: the direct object of the sentence
- indirect_object: the indirect object of the sentence

Format:
- Return well-formed JSON.  Do not include any other text or comments.  Do not include trailing commas.
"""
