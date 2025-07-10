def generate_tense_list_prompt() -> str:
    return ""


def generate_verb_tense_format() -> str:
    return """ \
                {   \
                    verb tense (as tense): \
                    conjugations: [ \
                        {  \
                            french pronoun (as 'pronoun'): \
                            conjugated verb, without its pronoun (as 'verb'):    \
                            english translation (as 'translation'): \
                        }  \
                    ]   \
                } \
"""


def generate_extra_rules() -> str:
    return """Do not return as a fenced code block. \
            Do not return any newlines in the response. \
            Do not include reflexive pronouns in the pronoun field. \
            Always use both genders in the 3rd person pronouns.  \
            Always include 'on' for the 3rd person singular form.  \
            Replace spaces with _ in the tense names. \
            Remove all accent marks on the tense names. \
            The first person pronoun should always be 'je' instead of j' or j. \
            The pronouns should always be "-" for participles. \
            All json property names and values need to be enclosed in double quotes. \
            The tenses 'past_participle', 'participe_passe', 'passecompose', 'past_compose', and 'participe' should always be renamed 'participle' \
            """


def generate_verb_prompt(verb_infinitive: str):
    return f"""Give me the present, passé composé (as passe_compose), imparfait, future simple tense, \
            and past participle (as participle), and auxiliary verb of the French verb {verb_infinitive}, \
            with english translations, with each verb mode being a json object of the format: \
                auxiliary: \
                infinitive: {verb_infinitive} \
                verb tense (as 'tenses'): [ \
                    {generate_verb_tense_format()} \
                ] \
            {generate_extra_rules()}
            """
