from dbtest.sentences.models import DirectObject, IndirectPronoun, Negation

class SentencePromptGenerator: 
    # pylint: disable=too-few-public-methods, line-too-long

    def __complement_objects(self, sentence):
        if sentence.direct_object is not DirectObject.none and sentence.indirect_pronoun is IndirectPronoun.none:
            return f"The sentence must have a direct object as a pronoun in the first clause before the verb {sentence.infinitive}."
        if sentence.direct_object is DirectObject.none and sentence.indirect_pronoun is not IndirectPronoun.none:
            return f"The sentence must have an indirect object as a pronoun in the first clause before the verb {sentence.infinitive}."
        if sentence.direct_object is not DirectObject.none and sentence.indirect_pronoun is not IndirectPronoun.none:
            return f"The sentence must have both a direct object as a pronoun and an indirect object as a pronoun in the first clause before the verb {sentence.infinitive}."
        return ""

    def __negatedness(self, sentence):
        return f"The sentence must contain the negation {sentence.negation.prompt}." if sentence.negation is not Negation.none else ""

    def __verb_properties(self, sentence):
        return f"The sentence has the verb infinitive {sentence.infinitive} in the {sentence.tense.prompt} tense, and may start with a {sentence.pronoun.prompt} subject pronoun."

    def __sentence_correctness(self, sentence):
        return "The sentence should be correctly formed." if sentence.is_correct else "The sentence should contain exactly one error in the pronoun, verb, objects, or negation." #  There must be only one clause."

    def __translation(self, sentence):
        return "The response should include an English translation." if sentence.is_correct else "The response should not include a translation."

    def __detect_objects(self):
        return "If the generated sentence has a COD, set has_direct_object in the response to true.  Otherwise set it to false.  If the generated sentence has a COI, set the has_indirect_pronoun property to true.  Otherwise set it to false."

    def __transform_nouns_to_pronouns(self):
        return "Transform any COD and COI nouns in the sentence into their respective pronouns."

    def __json_format(self):
        return """The response should be returned as json in the format:
    {
        "sentence": "",
        "translation": "",
        "is_correct": "",
        "has_direct_object": "",
        "has_indirect_pronoun": ""
    }
    """

    def __correct_elisions(self):
        return "The sentence should have correct French elisions.  This includes que and qui connectors."

    def __extra_rules(self):
        return "The JSON must be properly formatted, with all properties and values in double quotes."

    def generate_sentence_prompt(self, sentence) -> str:
        return '\n'.join([
                self.__complement_objects(sentence),
                self.__negatedness(sentence),
                self.__verb_properties(sentence),
                self.__sentence_correctness(sentence),
                self.__translation(sentence),
                self.__detect_objects(),
                self.__transform_nouns_to_pronouns(),
                self.__json_format(),
                self.__correct_elisions(),
                self.__extra_rules()
            ])
