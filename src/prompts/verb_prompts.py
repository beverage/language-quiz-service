class VerbPromptGenerator:
    """Generates prompts for the verb conjugation of a given verb."""

    def __init__(self):
        pass

    def _get_objects_prompt(self, verb_infinitive: str, auxiliary: str) -> str:
        return f"""
You are a French verb expert. Determine if the verb '{verb_infinitive}' with auxiliary '{auxiliary}' can take direct objects (COD) and/or indirect objects (COI) in its MOST COMMON usage.

Return this exact JSON format:
{{
    "can_have_cod": true,
    "can_have_coi": false
}}

CLASSIFICATION RULES:

=== COD ONLY (true, false) ===
Direct transitive verbs that take objects without prepositions:
- manger (quelque chose), voir (quelqu'un), prendre (quelque chose)
- faire (quelque chose), avoir (quelque chose), lire (quelque chose)

=== COI ONLY (false, true) ===
Verbs that REQUIRE prepositions (à, de, etc.) for their objects:
- téléphoner (à quelqu'un), répondre (à quelqu'un), obéir (à quelqu'un)
- penser (à quelque chose), réfléchir (à quelque chose), ressembler (à quelqu'un)
- réussir (à quelque chose), appartenir (à quelqu'un), plaire (à quelqu'un)

=== BOTH COD AND COI (true, true) ===
Ditransitive verbs with pattern "verb + direct object + à/de + indirect object":
- donner (quelque chose à quelqu'un), dire (quelque chose à quelqu'un)
- promettre (quelque chose à quelqu'un), enseigner (quelque chose à quelqu'un)
- servir (quelque chose à quelqu'un), offrir (quelque chose à quelqu'un)
- vendre (quelque chose à quelqu'un), prêter (quelque chose à quelqu'un)
- apprendre (quelque chose à quelqu'un), montrer (quelque chose à quelqu'un)

=== NEITHER (false, false) ===
Intransitive verbs with no complement objects:
- aller, venir, arriver, partir, rester, naître, mourir
- dormir, rire, sourire, être, exister

AUXILIARY-SPECIFIC USAGE:
For verbs with multiple auxiliaries, consider the specified auxiliary:
- vivre + avoir: "J'ai vécu une expérience" → COD only
- sortir + avoir: "J'ai sorti les poubelles" → COD only  
- sortir + être: "Je suis sorti" → NEITHER

Focus on the MOST COMMON usage with the given auxiliary '{auxiliary}'.
"""

    def _get_verb_prompt(
        self, verb_infinitive: str, target_language_code: str = "eng"
    ) -> str:
        return f"""
You are a French verb conjugation expert. Your task is to provide a complete and valid JSON object representing the verb '{verb_infinitive}' according to the `LLMVerbPayload` Pydantic schema. You MUST populate ALL fields, including the repeating fields in the `tenses` array.

Tenses must be named exactly as follows:
- 'present'
- 'passe_compose'
- 'imparfait'
- 'future_simple'
- 'conditionnel'
- 'subjonctif'
- 'imperatif'

The JSON structure MUST be as follows. Do not deviate.

{{
    "infinitive": "{verb_infinitive}",
    "target_language_code": "{target_language_code}",
    "auxiliary": "être" or "avoir",
    "reflexive": true or false,
    "translation": "English translation of the verb",
    "past_participle": "The past participle of the verb",
    "present_participle": "The present participle of the verb",
    "classification": "third_group",
    "is_irregular": true,

    "tenses": [
        {{
            "infinitive": "{verb_infinitive}",
            "auxiliary": "être" or "avoir",
            "reflexive": true or false,
            "tense": "present",
            "first_person_singular": "",
            "second_person_singular": "",
            "third_person_singular": "",
            "first_person_plural": "",
            "second_person_plural": "",
            "third_person_plural": ""
        }},
        {{
            "infinitive": "{verb_infinitive}",
            "auxiliary": "être" or "avoir",
            "reflexive": true or false,
            "tense": "passe_compose",
            "first_person_singular": "",
            "second_person_singular": "",
            "third_person_singular": "",
            "first_person_plural": "",
            "second_person_plural": "",
            "third_person_plural": ""
        }}
    ]
}}

Guidelines:
- Provide conjugations for all tenses listed above.
- Do not include the pronoun in the conjugations themselves.
- The `classification` field MUST be one of 'first_group', 'second_group', or 'third_group'.
- The `infinitive`, `auxiliary`, and `reflexive` fields MUST be repeated for each object in the `tenses` array.
- For reflexive verbs (e.g., 'se laver'), set `reflexive` to true, but do not include the pronoun in the conjugations themselves.
- Return only well-formed JSON. No extra text, comments, or trailing commas.
"""

    def generate_objects_prompt(self, verb_infinitive: str, auxiliary: str) -> str:
        return self._get_objects_prompt(verb_infinitive, auxiliary)

    def generate_verb_prompt(
        self, verb_infinitive: str, target_language_code: str = "eng"
    ) -> str:
        return self._get_verb_prompt(verb_infinitive, target_language_code)
