class VerbPromptGenerator:
    """Generates prompts for the verb conjugation of a given verb."""

    def __init__(self):
        pass

    VERB_PROMPT = """
You are a French verb conjugation expert. Your task is to provide a complete and valid JSON object representing the verb '{infinitive}' according to the `LLMVerbPayload` Pydantic schema. You MUST populate ALL fields, including the repeating fields in the `tenses` array.

Tenses must be named exactly as follows:
- 'present'
- 'passe_compose'
- 'imparfait'
- 'future_simple'
- 'conditionnel'
- 'subjunctive'
- 'imperative'

The JSON structure MUST be as follows. Do not deviate.

{{
    "infinitive": "{infinitive}",
    "target_language_code": "fra",
    "auxiliary": "être" or "avoir",
    "reflexive": true or false,
    "translation": "English translation of the verb",
    "past_participle": "The past participle of the verb",
    "present_participle": "The present participle of the verb",
    "classification": "third_group",
    "is_irregular": true,
    "tenses": [
        {{
            "infinitive": "{infinitive}",
            "auxiliary": "être" or "avoir",
            "reflexive": true or false,
            "tense": "present",
            "first_person_singular": "",
            "second_person_singular": "",
            "third_person_singular": "",
            "first_person_plural": "",
            "second_person_formal": "",
            "third_person_plural": ""
        }},
        {{
            "infinitive": "{infinitive}",
            "auxiliary": "être" or "avoir",
            "reflexive": true or false,
            "tense": "passe_compose",
            "first_person_singular": "",
            "second_person_singular": "",
            "third_person_singular": "",
            "first_person_plural": "",
            "second_person_formal": "",
            "third_person_plural": ""
        }}
    ]
}}

Guidelines:
- Provide conjugations for all tenses listed above.
- The `classification` field MUST be one of 'first_group', 'second_group', or 'third_group'.
- The `infinitive`, `auxiliary`, and `reflexive` fields MUST be repeated for each object in the `tenses` array.
- For reflexive verbs (e.g., 'se laver'), set `reflexive` to true, but do not include the pronoun in the conjugations themselves.
- Return only well-formed JSON. No extra text, comments, or trailing commas.
"""

    def generate_verb_prompt(self, verb_infinitive: str) -> str:
        return self.VERB_PROMPT.format(infinitive=verb_infinitive)
