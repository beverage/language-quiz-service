from dbtest.sentences.models import DirectObject, IndirectPronoun, Negation

class SentencePromptGenerator: 
    # pylint: disable=too-few-public-methods, line-too-long

    def __complement_objects(self, sentence):
        #   TODO: Random inputs produce 'random' in the outputs.  This needs to be fixed.
        if sentence.direct_object is not DirectObject.none and sentence.indirect_pronoun is IndirectPronoun.none:
            return f"The sentence must have a complement object direct in the first clause before the verb {sentence.infinitive}."
        if sentence.direct_object is DirectObject.none and sentence.indirect_pronoun is not IndirectPronoun.none:
            return f"The sentence must have a complement object indirect in the first clause before the verb {sentence.infinitive}."
        if sentence.direct_object is not DirectObject.none and sentence.indirect_pronoun is not IndirectPronoun.none:
            return f"The sentence must have both a complement object direct and an complement object indirect in the first clause before the verb {sentence.infinitive}."
        return ""

    def __negatedness(self, sentence):
        #   TODO: This needs to not be using the hardcoded string.
        return f"The sentence must contain the negation {sentence.negation}." if sentence.negation != "none" else "The sentence must not contain any negation."

    def __verb_properties(self, sentence):
        return f"The sentence has the verb infinitive {sentence.infinitive} in the {sentence.tense.prompt} tense, and may start with a {sentence.pronoun.prompt} subject pronoun."

    def __sentence_correctness(self, sentence):
        if sentence.is_correct is False:
            if sentence.direct_object is DirectObject.none and sentence.indirect_pronoun is IndirectPronoun.none and sentence.negation is Negation.none:
                return "The sentence must contain an error in its pronoun or verb conjugation."
            else:
                return "The sentence must contain an error in any of its direct objects, indirect pronouns, or negations."
        else:
            return "The sentence should be correctly formed."

    def __translation(self, sentence):
        return "The response should include an English translation." if sentence.is_correct else "The response should not include a translation."

    def __detect_objects(self):
        #   TODO: This will never work as long as the input JSON remains in a pure string format.
        return "If the generated sentence has a complement object direct, set has_direct_object in the response to true.  Otherwise set it to an empty string.  If the generated sentence has a complement object indirect, set the has_indirect_pronoun property to true.  Otherwise set it to an empty string."

    def __detect_negations(self):
        #   TODO: This needs to be smarter, and plug in supported negations directly.
        return "If the sentence has any French language negation present, set is_negated in the response to True.  Otherwise set it to an empty string."

    def __transform_nouns_to_pronouns(self):
        return "Transform any COD and COI nouns in the sentence into their respective pronouns."

    def __json_format(self):
        return """The response should be returned as raw json in the format.  All six fields must be present.  Do not wrap the json codes in JSON markers.
    {
        "sentence": "",
        "translation": "",
        "is_correct": "",
        "is_negated": "",
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
                self.__detect_negations(),
                self.__transform_nouns_to_pronouns(),
                self.__json_format(),
                self.__correct_elisions(),
                self.__extra_rules()
            ])
