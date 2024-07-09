
class SentencePromptGenerator:

    def __verb_properties(self, sentence):
        pronoun = sentence.pronoun.name.replace('_', ' ')
        tense = sentence.tense.name.replace('_', ' ')
        return f"""Generate a sentence in French with exactly the verb infinitive {sentence.infinitive}, the pronoun in the {pronoun}, in the {tense} tense."""        

    def __sentence_correctness(self, sentence):
        return "The sentence should be correctly formed." if sentence.is_correct else "The sentence should contain exactly one error in the pronoun or verb.  After the verb, the remaining text should not be in accordance with the verb and pronouns.  There must be only one clause."

    def __translation(self, sentence):
        return "The response should include an English translation." if sentence.is_correct else "The response should not include a translation."

    def __json_format_rule(self):
        return """The response should be returned as json in the format:
    {
        sentence:
        translation:
        is_correct:
    }
    """

    def __extra_rules(self):
        return """The JSON must be properly formatted, with all properties and values in double quotes."""

    def generate_sentence_prompt(self, sentence):
        return '\n'.join([
                self.__verb_properties(sentence),
                self.__sentence_correctness(sentence),
                self.__translation(sentence),
                self.__json_format_rule(),
                self.__extra_rules()])
