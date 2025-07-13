from src.schemas.sentences import DirectObject, IndirectObject, Negation, SentenceBase
from src.schemas.verbs import Verb


class SentencePromptGenerator:
    """Generates prompts for the sentence of a given verb."""

    def __init__(self):
        pass

    def _get_sentence_prompt(
        self, sentence: SentenceBase, verb: Verb, sentence_properties: str
    ) -> str:
        return f"""
You are a French grammar expert. Construct a creative and varied sentence in French with the following properties:

{sentence_properties}

CREATIVITY INSTRUCTIONS:
- Create diverse, interesting sentences that vary in vocabulary, structure, and context
- Use different subjects, objects, and contexts to avoid repetition
- Include varied vocabulary (people, places, objects, activities, emotions, etc.)
- Vary sentence length and complexity when appropriate
- If the verb allows additional complements or infinitives, consider adding them for variety
- Make sentences contextually interesting and realistic

{{
    "sentence": "",
    "translation": "",
    "is_correct": "true or false",
    "explanation": "",
    "negation": "none, pas, jamais, rien, personne, plus, aucune, or encore",
    "direct_object": "none, masculine, feminine, or plural",
    "indirect_object": "none, masculine, feminine, or plural",
    "has_compliment_object_direct": "true or false",
    "has_compliment_object_indirect": "true or false",
}}

Rules:
- The sentence must semantically and idiomatically make sense.
- All prepositions match their indirect, or subordinate pronouns.
- If the verb requires additional objects or infinitives afterwards, add some for variety and completeness.
- If the sentence generated does not have a complement object direct, or {verb.can_have_cod} is false, set direct_object to "none", and set has_compliment_object_direct to false.
- If the sentence generated does not have a complement object indirect, or {verb.can_have_coi} is false, set indirect_object to "none", and set has_compliment_object_indirect to false.
- If the conjugation uses the participle, and the auxiliary is 'être', make sure the number and gender match the subject.
- If verb is reflexive, use the reflexive pronoun in the sentence.
- If the sentence is not grammatically correct, provide a brief explanation of why this sentence is grammatically incorrect.

Field Instructions:
- direct_object: Return the grammatical gender/number of the direct object ("masculine", "feminine", "plural") or "none" if no direct object
- indirect_object: Return the grammatical gender/number of the indirect object ("masculine", "feminine", "plural") or "none" if no indirect object  
- negation: Return ONLY actual negation words ("pas", "jamais", "rien", "personne", "plus", "aucun", "aucune", "encore") or "none" if no negation. Do NOT use positive adverbs like "toujours", "souvent", "déjà" in this field.
- Do NOT put actual object words (like "un livre", "la porte") in direct_object or indirect_object fields
- Feel free to use adverbs and other descriptive words to make sentences more interesting, but keep negation field accurate

Format:
- Check all elisions are correct.  Examples: 'Je habite' -> 'J'habite', or 'Est-ce que il est là' -> 'Est-ce qu'il est là.'
- Check all capitalization is correct.
- Return the translation in {sentence.target_language_code}.
- Return well-formed JSON.  Do not include any other text or comments.  Do not include trailing commas.
"""

    def __sentence_properties(self, sentence: SentenceBase, verb: Verb) -> str:
        return f"""The sentence uses {sentence.pronoun.value} as the subject.
The sentence uses {sentence.tense.value} as the tense.
The sentence uses {verb.infinitive} as the verb.
The sentence uses {verb.auxiliary} as the auxiliary.
"""

    def __compliment_object_direct(self, sentence: SentenceBase, verb: Verb) -> str:
        return f"""
The sentance must contain a {sentence.direct_object.value} compliment direct object before the verb if the verb {verb.can_have_cod} is true.
A compliment direct object is a direct object that is not the actual direct object, comes before the verb, and is either le, la, or les.  It
replaces the actual direct object.
    """

    def __compliment_object_indirect(self, sentence: SentenceBase, verb: Verb) -> str:
        return f"""
The sentence must contain an {sentence.indirect_object.value} compliment indirect object before the verb if the verb {verb.can_have_coi} is true.
A compliment indirect object is an indirect object that is not the actual indirect object, comes before the verb, and is either lui, la, or leur.  It
replaces the actual indirect object.
    """

    def __negation(self, sentence):
        return f"""The sentence must contain the negation {sentence.negation.value}."""

    def __correctness(self, sentence: SentenceBase) -> str:
        if not sentence.is_correct:
            prompt = [
                """
The sentence will contain one or more SUBTLE grammatical errors while maintaining the same level of creativity, 
complexity, and length as a correct sentence. These errors can include incorrect conjugation, number and 
gender disagreements, incorrect object agreement, incorrect pronoun agreement, incorrect auxiliary agreement, etc.

IMPORTANT: The incorrect sentence should be just as elaborate, descriptive, and creative as a correct sentence would be.
Use rich vocabulary, complex structures, and interesting contexts, but embed the grammatical errors within this complexity.
Do not make the sentence shorter or simpler just because it's incorrect.
"""
            ]
            if sentence.direct_object != DirectObject.NONE:
                prompt.append("The complement object should be incorrect.")

            if sentence.indirect_object != IndirectObject.NONE:
                prompt.append("The indirect pronoun should be incorrect.")

            return "\n".join(prompt)
        else:
            return """The sentence will be grammatically correct."""

    def generate_sentence_prompt(self, sentence: SentenceBase, verb: Verb) -> str:
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
            sentence, verb, sentence_properties="\n".join(sentence_properties)
        )

    def generate_correctness_prompt(self, sentence: SentenceBase, verb: Verb) -> str:
        return f"""
You are a French grammar expert. Review the following sentence for grammatical, idiomatic, and semantic correctness.

Sentence: {sentence.content}

Required properties:
- Subject: {sentence.pronoun.value}
- Tense: {sentence.tense.value} 
- Verb: {verb.infinitive}
- Auxiliary: {verb.auxiliary}
- COD: {"required" if sentence.direct_object.value != "none" and verb.can_have_cod else "not required"}
- COI: {"required" if sentence.indirect_object.value != "none" and verb.can_have_coi else "not required"}
- Correctness: {"must be incorrect" if not sentence.is_correct else "must be correct"}

Return JSON with these fields:
- is_valid: true if sentence meets all requirements above
- explanation: brief explanation if is_valid is false
- actual_direct_object: none, masculine, feminine, or plural
- actual_indirect_object: none, masculine, feminine, or plural  
- actual_negation: detected negation type or none
- direct_object_text: the actual direct object word(s) found
- indirect_object_text: the actual indirect object word(s) found

Return only valid JSON, no other text.
"""
