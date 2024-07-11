from dbtest.database.sentences import DirectObject

class SentencePromptGenerator:

    def __direct_object(self, sentence):
        return f"The sentence must have the pronoun {sentence.pronoun}.  After the pronoun, the sentence must have a clitic {sentence.direct_pronoun.name} pronouns before the verb {sentence.infinitive}."
        # return f"With the pronoun {sentence.pronoun}, the sentence must have a direct complement object before the verb." if sentence.direct_object else ""
        # return f"The sentence must not have an object after the verb.  It should have the direct object {sentence.direct_object.name} before the verb." if sentence.direct_object else ""
        # return f"The sentence should replace its object after the verb with the direct object {sentence.direct_object.name}." if sentence.direct_object else ""
        # return f"The sentence is required to have a {sentence.direct_object.name} direct object after the pronoun, and before any verbs, and no direct objects after {sentence.infinitive}." if sentence.direct_pronoun is not DirectObject.none else ""

    def __verb_properties(self, sentence):
        pronoun = sentence.pronoun.name.replace('_', ' ')
        tense = sentence.tense.name.replace('_', ' ')
        return f"""Generate a sentence in French with exactly the verb infinitive {sentence.infinitive}, the pronoun in the {pronoun}, in the {tense} tense."""        

    def __sentence_correctness(self, sentence):
        return "The sentence should be correctly formed." if sentence.is_correct else "The sentence should contain exactly one error in the pronoun or verb or objects.  After the verb, the remaining text should not be in accordance with the verb and pronouns and objects.  There must be only one clause."

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
                # self.__indirect_object(sentence),
                # self.__pronominal_adverbs(sentence),
                self.__verb_properties(sentence),
                self.__sentence_correctness(sentence),
                self.__translation(sentence),
                self.__json_format_rule(),
                self.__correct_elisions(),
                self.__extra_rules()])
