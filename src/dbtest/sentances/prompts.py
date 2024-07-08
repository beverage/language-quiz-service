from dbtest.database.metadata import Base

#
#   There would be a lot of common functionality for other prompt generators.  Abstract this.
#   Lots of interesting ideas here.  Could this take just a partial configuration and generate
#   lots of random correct/incorrect sentences around a common template perhaps?
#
class SentencePromptGenerator:
    
    def __init__(self):
        self.Sentence = Base.classes.sentences
        
    def __generate_sentence_prompt_verb_properties(self, sentence):
        pronoun = sentence.pronoun.name.replace('_', ' ')
        tense = sentence.tense.name.replace('_', ' ')
        return f"""Generate a sentence in French with the verb infinitive {sentence.infinitive}, the pronoun in the {pronoun}, in the {tense} tense."""        
                
    def __generate_sentence_correctness_prompt(self, sentence):
        return "The sentence should be correctly formed." if sentence.is_correct else "The sentence should contain an error."

    def __generate_translation_prompt(self, sentence):
        return "The response should include an English translation." if sentence.is_correct else None

    def __generate_format_prompt(self, sentence):
        return """The response should be returned as json in the format:
    {
        sentence:
        translation:
        is_correct:
    }
    """

    def generate_sentence_prompt(self, sentence):
        return '\n'.join([
                self.__generate_sentence_prompt_verb_properties(sentence),
                self.__generate_sentence_correctness_prompt(sentence),
                self.__generate_translation_prompt(sentence),
                self.__generate_format_prompt(sentence)])
