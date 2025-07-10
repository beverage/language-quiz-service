from schemas.sentence import DirectObject, IndirectPronoun, Negation


class SentencePromptGenerator:
    # pylint: disable=too-few-public-methods, line-too-long

    def __complement_object_direct(self, sentence):
        if sentence.direct_object != DirectObject.NONE:
            return f"The sentence must return a COD (direct object) of gender {sentence.direct_object} if it is possible to do with the verb {sentence.infinitive}."
        else:
            return f"The sentence must not contain a COD (direct object) unless the verb {sentence.infinitive} requires it."

    def __complement_pronoun_indirect(self, sentence):
        if sentence.indirect_pronoun != IndirectPronoun.NONE:
            return f"The sentence must return a COI (indirect pronoun) of gender {sentence.indirect_pronoun} with the verb {sentence.infinitive} if possible to do with the verb {sentence.infinitive}."
        else:
            return f"The sentence must not contain a COI (indirect pronoun) unless the verb {sentence.infinitive} requires it."

    def __pronoun_ordering(self):
        return "If the sentence has a COD (direct object) and a COI (indirect pronoun), put them in the right order.  Switch them if necessary."

    def __negatedness(self, sentence):
        if sentence.negation != Negation.NONE:
            return "  ".join(
                [
                    f"The sentence must contain the negation {sentence.negation}.",
                    "'Ne' must always come before any direct objects or indirect pronouns.  The negation must come directly after the object.",
                ]
            )
        else:
            return "The sentence must not contain a negation."

    def __verb_properties(self, sentence):
        return f"The sentence has the verb infinitive {sentence.infinitive} in the {sentence.tense.value} tense, and may start with a {sentence.pronoun.value} subject pronoun."

    def __verb_compliments(self):
        return "If the verb requires additional objects or infinitives afterwards, add some.  They must agree in gender and number."

    def __prepositions(self):
        return "All prepositions match their indirect, or subordinate pronouns."

    def __sentence_correctness(self, sentence):
        if sentence.is_correct is False:
            if (
                sentence.direct_object is DirectObject.NONE
                and sentence.indirect_pronoun is IndirectPronoun.NONE
                and sentence.negation is Negation.NONE
            ):
                return "The sentence must contain an error in its pronoun or verb conjugation."
            else:
                return "The sentence must contain an error in any of its direct objects, indirect pronouns, negations, or prepositions, ordering."
        else:
            return "The sentence should be correctly formed."

    def __translation(self, sentence):
        if sentence.is_correct:
            return "The response should include an English translation."
        else:
            # If content exists, use it in the error message; otherwise use a generic message
            if hasattr(sentence, "content") and sentence.content:
                return f"The 'translation' field should be a short reason why '{sentence.content}' is incorrect.  Do not repeat '{sentence.content}' in the output.  Return only the reason."
            else:
                return "The 'translation' field should be a short reason why the sentence is incorrect."

    def __detect_negations(self):
        #   TODO: This needs to be smarter, and plug in supported negations directly.
        return "If the sentence has any French language negation present, set is_negated in the response to 'True'.  Otherwise set it to 'False'."

    def __json_format(self):
        return """The response should be returned as raw json in the format below.  All six fields must be present.  Do not use json code fencing.
    {
        "sentence": "",
        "translation": "",
        "is_correct": "",
        "negation": "",
        "direct_object": "",
        "indirect_pronoun": ""
    }
    """

    def __set_negation_field(self, sentence):
        return "If the sentence contains a negation, set the 'negation' field in the response to that negation, without any 'ne', or 'n'' prefix.  If the negation is two words, use only the first word.  If the sentence is not negated, or 'False' is returned, set it to 'none'"

    def __set_object_type_field(self, object_type, object_name):
        return f"If the generated sentence has a {object_type}, set {object_name} to 'masculine if it is masculine', 'feminine' if it is feminine, or 'plural' if it is plural.  Set it to 'none' if it does not have an {object_name}."

    def __correct_elisions(self):
        return "The sentence should have correct French elisions.  This includes que, and qui connectors.  This includes 'n'' negations."

    def __extra_rules(self):
        # TODO: we should not have an oddly specific rule around the word 'random'.  This is a hack to get around poor enum handling for now.
        return "The JSON must be properly formatted, with all properties and values in double quotes.  The sentence must not include the word 'random'."

    def generate_sentence_prompt(self, sentence) -> str:
        return "\n".join(
            [
                self.__complement_object_direct(sentence),
                self.__complement_pronoun_indirect(sentence),
                self.__pronoun_ordering(),
                self.__negatedness(sentence),
                self.__verb_properties(sentence),
                self.__verb_compliments(),
                self.__prepositions(),
                self.__sentence_correctness(sentence),
                self.__translation(sentence),
                self.__detect_negations(),
                self.__json_format(),
                self.__set_negation_field(sentence),
                self.__set_object_type_field("COD", "direct_object"),
                self.__set_object_type_field("COI", "indirect_pronoun"),
                self.__correct_elisions(),
                self.__extra_rules(),
            ]
        )

    def validate_french_sentence_prompt(self, sentence) -> str:
        return f"Is the sentence '{sentence.content}' grammatically correct in terms of French syntax, verb usage, object placement, pronoun placement, and preposition usage? If it is correct for all, return 'True', or if not, return 'False'."

    def correct_sentence_prompt(self, sentence) -> str:
        correction_prompt: str = "\n".join(
            [
                f"Correct any grammatical errors in the sentence '{sentence.content}' in terms of French syntax, verb usage, direct object placement, indirect pronoun placement, and preposition usage.",
                """The response should be returned as raw json in the format below.  Both fields must be present.  Do not return as a fenced code block.
    {
        "corrected_sentence": "",
        "corrected_translation": ""
    }
    """,
                "Return only the corrected sentence as 'corrected_sentence'.  Return a corrected translation as 'corrected_translation'.",
            ]
        )

        return correction_prompt
