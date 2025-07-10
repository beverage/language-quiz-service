from schemas.sentence import DirectObject, IndirectPronoun, Negation, Sentence


class SentencePromptGenerator:
    """Generates prompts for the sentence of a given verb."""

    def __init__(self):
        pass

    SENTENCE_PROMPT = """
You are a French grammar expert.  Construct a sentence in French with the following properties:

{sentence_properties}

{{
    "sentence": "",
    "translation": "",
    "is_correct": "true or false",
    "negation": "",
    "direct_object": "none, masculine, feminine, or plural",
    "indirect_pronoun": "none, masculine, feminine, or plural"
}}

Rules:
- If the sentence has a direct object and an indirect pronoun, put them in the right order.  Switch them if necessary.
- If the sentence contains any negation, set the negation field to true.
- Check all elisions are correct.  Examples: 'Je habite' -> 'J'habite', or 'Est-ce que il est là' -> 'Est-ce qu'il est là.'
- All prepositions match their indirect, or subordinate pronouns."
- If the verb requires additional objects or infinitives afterwards, add some.  They must agree in gender and number.
- If the conjugation uses the participle, and the auxiliary is 'être', make sure the number and gender match the subject.
- If verbis reflexive, use the reflexive pronoun in the sentence.
- If the phrase is negatated, return either the precise negation (pas, jamais, rien, etc.), or 'none'.

Format:
- Return well-formed JSON.  Do not include any other text or comments.  Do not include trailing commas.
- Return the sentence in the language of the sentence properties.
- Return the translation in the language of the sentence properties.
- Return the is_correct as a boolean.
- Return the negation as a string.
- Return the direct_object as a string.  Either masculine, feminine, plural, or none.
- Return the indirect_pronoun as a string.  Either masculine, feminine, plural, or none.
- Return well-formed JSON.  Do not include any other text or comments.  Do not include trailing commas.
"""

    def __sentence_properties(self, sentence: Sentence) -> str:
        return f"""The sentence uses {sentence.pronoun.value} as the subject.
The sentence uses {sentence.tense.value} as the tense.
The sentence uses {sentence.infinitive} as the verb.
The sentence uses {sentence.auxiliary} as the auxiliary.
"""

    def __compliment_object_direct(self, sentence: Sentence) -> str:
        return f"""The sentance must contain a {sentence.direct_object.value} direct object before the verb if the verb {sentence.infinitive} allows it.
    """

    def __compliment_object_indirect(self, sentence: Sentence) -> str:
        return f"""The sentence must contain an {sentence.indirect_pronoun.value} indirect pronoun before the verb if the verb {sentence.infinitive} allows it.
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
                prompt.append("The complement object may be incorrect.")

            if sentence.indirect_pronoun != IndirectPronoun.NONE:
                prompt.append("The indirect pronoun may be incorrect.")

            return "\n".join(prompt)
        else:
            return """The sentence will be grammatically correct."""

    def generate_sentence_prompt(self, sentence: Sentence) -> str:
        sentence_properties = [self.__sentence_properties(sentence)]

        if sentence.direct_object != DirectObject.NONE:
            sentence_properties.append(self.__compliment_object_direct(sentence))

        if sentence.indirect_pronoun != IndirectPronoun.NONE:
            sentence_properties.append(self.__compliment_object_indirect(sentence))

        if sentence.negation != Negation.NONE:
            sentence_properties.append(self.__negation(sentence))

        return self.SENTENCE_PROMPT.format(
            sentence_properties="\n".join(sentence_properties)
        )
