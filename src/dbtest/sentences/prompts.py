from dbtest.sentences.models import DirectObject, IndirectPronoun, Negation

class SentencePromptGenerator: 
    # pylint: disable=too-few-public-methods, line-too-long

    def __complement_object(self, object_type, object_value, sentence):
        if object_value != "none":
            if object_value == "random":
                return f"The sentence may randomly contain a masculine, feminine, or plural {object_type} in its first clause."
            else:
                return f"The sentence must contain a {object_value} {object_type} in its first clause before the verb {sentence.infinitive}."
        else:
            return f"The sentence must not contain a {object_type}."

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

    def __detect_negations(self):
        #   TODO: This needs to be smarter, and plug in supported negations directly.
        return "If the sentence has any French language negation present, set is_negated in the response to 'True'.  Otherwise set it to 'False'."

    def __json_format(self):
        return """The response should be returned as raw json in the format.  All six fields must be present.  Do not wrap the json codes in JSON markers.
    {
        "sentence": "",
        "translation": "",
        "is_correct": "",
        "negation": "",
        "direct_object": "",
        "indirect_pronoun": ""
    }
    """

    def __set_negation_field(self):
        return "If the sentence contains a negation, set the negation field to that negation without the 'ne' prefix.  Otherwise set it to None"

    def __set_object_type_field(self, object_type, object_name):
        return f"If the generated sentence has a {object_type}, set {object_name} to 'masculine if it is masculine', 'feminine' if it is feminine, or 'plural' if it is plural.  Set it to 'none' if it does not have an {object_name}."

    def __correct_elisions(self):
        return "The sentence should have correct French elisions.  This includes que and qui connectors."

    def __extra_rules(self):
        # TODO: we should not have an oddly specific rule around the word 'random'.  This is a hack to get around poor enum handling for now.
        return "The JSON must be properly formatted, with all properties and values in double quotes.  The sentence must not include the word 'random'."

    def generate_sentence_prompt(self, sentence) -> str:
        return '\n'.join([
                self.__complement_object("COD", sentence.direct_object, sentence),
                self.__complement_object("COI", sentence.indirect_pronoun, sentence),
                self.__negatedness(sentence),
                self.__verb_properties(sentence),
                self.__sentence_correctness(sentence),
                self.__translation(sentence),
                self.__detect_negations(),
                self.__json_format(),
                self.__set_negation_field(),
                self.__set_object_type_field("COD", "direct_object"),
                self.__set_object_type_field("COI", "indirect_pronoun"),
                self.__correct_elisions(),
                self.__extra_rules()
            ])
