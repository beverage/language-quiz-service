class VerbPromptGenerator:
    """Generates prompts for the verb conjugation of a given verb."""

    def __init__(self):
        pass

    VERB_PROMPT = """
You are a French verb conjugation expert.  Provide the conjugation of the French verb {infinitive} in the following format:

Tenses:
- presént: named exactly as 'present'
- passé composé: named exactly as 'passe_compose'
- imparfait: named exactly as 'imparfait'
- futur simple: named exactly as 'future_simple'
- conditionnel présent: named exactly as 'conditional'
- subjonctif présent: named exactly as 'subjunctive'
- impératif présent: named exactly as 'imperative'

{{
    "infinitive": "{infinitive}",
    "auxiliary": "être" or "avoir",
    "reflexive": true or false,
    "past_participle": "the participe paseé of the verb",
    "present_participle": "the present participle of the verb",
    "is_irregular": true or false,
    "translation": "the translation of the verb infinitive",
    "tenses": [
        {{
            "tense": "",
            "conjugations":
            {{
                "first_person_singular": "",
                "second_person_singular": "",
                "third_person_singular": "",
                "first_person_plural": "",
                "second_person_formal": "",
                "third_person_plural": "",
            }}
        }},
    ]
}}

Guidelines:
- Get the conjugation for all tenses listed above if they exist for the verb {infinitive}.
- If the verb is reflexive and the infinitive starts with 'se', set the reflexive property to true.
- Do not include the reflexive pronoun in the conjugation.
- Return the tense names exactly as they are listed above.
- If the verb is irregular in French, set the is_irregular property to true.  Verbs etre, avoir, aller, venir, etc. are irregular.
- For verbs with auxiliary 'être', do not include gender or number hints on the participe paseé.  No (e) or (s) or (es).
- Return well-formed JSON.  Do not include any other text or comments.  Do not include trailing commas.
"""

    def generate_verb_prompt(self, verb_infinitive: str) -> str:
        return self.VERB_PROMPT.format(infinitive=verb_infinitive)
