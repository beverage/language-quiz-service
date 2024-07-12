
class SentencePromptGenerator:

    def __direct_object(self, sentence):
        return f"The sentence must have a {sentence.direct_object.prompt} object before the verb {sentence.infinitive}, and any indirect pronoun, and before {sentence.infinitive}."

    def __indirect_object(self, sentence):
        return f"The sentence must have a dative {sentence.indirect_object.prompt} pronoun before the verb {sentence.infinitive}, and after any direct object, and before {sentence.infinitive}."

    def __dual_objects(self, sentence):
        return f"The sentence must include both a clitic {sentence.direct_object.prompt} object and a dative {sentence.indirect_object.prompt} pronoun." if sentence.direct_object and sentence.indirect_object else ""

    def __verb_properties(self, sentence):
        return f"""The sentence has the verb infinitive {sentence.infinitive}, and a {sentence.pronoun.prompt} subject pronoun in the {sentence.tense.prompt} tense."""        

    def __sentence_correctness(self, sentence):
        return "The sentence should be correctly formed." if sentence.is_correct else "The sentence should contain exactly one error in the pronoun or verb or objects.  After the verb, the remaining text should be in accordance with the verb and pronouns and objects." #  There must be only one clause."

    def __translation(self, sentence):
        return "The response should include an English translation." if sentence.is_correct else "The response should not include a translation."

    def __json_format_rule(self):
        return """The response should be returned as json in the format:
    {
        "sentence": "",
        "translation": "",
        "is_correct": "",
    }
    """

    def __correct_elisions(self):
        return """The sentence should have correct French elisions."""

    def __extra_rules(self):
        return """The JSON must be properly formatted, with all properties and values in double quotes."""

    def generate_sentence_prompt(self, sentence):
        return '\n'.join([
                self.__direct_object(sentence),
                self.__indirect_object(sentence),
                self.__dual_objects(sentence),
                self.__verb_properties(sentence),
                self.__sentence_correctness(sentence),
                self.__translation(sentence),
                self.__json_format_rule(),
                self.__correct_elisions(),
                self.__extra_rules()])
