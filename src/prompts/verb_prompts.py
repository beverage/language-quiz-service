class VerbPromptGenerator:
    """Generates prompts for verb data extraction (properties, conjugations, objects)."""

    def __init__(self):
        pass

    def _get_verb_properties_prompt(
        self, verb_infinitive: str, target_language_code: str = "eng"
    ) -> str:
        """
        Generate prompt for extracting essential verb properties (no conjugations, no COD/COI).

        Used for adding new verbs to the database when migrations aren't practical.
        Returns: auxiliary, reflexive, translation, past_participle, present_participle,
                 classification, is_irregular
        """
        return f"""
You are a French verb expert. Your task is to provide essential properties for the verb '{verb_infinitive}'.

Return ONLY this JSON (no other text):
{{
    "infinitive": "{verb_infinitive}",
    "target_language_code": "{target_language_code}",
    "auxiliary": "avoir",
    "reflexive": false,
    "translation": "English translation",
    "past_participle": "past participle form",
    "present_participle": "present participle form",
    "classification": "first_group",
    "is_irregular": false
}}

CRITICAL RULES:
- The "auxiliary" field is REQUIRED and MUST be EXACTLY either "avoir" or "être" - NEVER leave it empty
- The "classification" field is REQUIRED and MUST be EXACTLY one of: "first_group", "second_group", or "third_group"
- The "reflexive" field is REQUIRED and MUST be a boolean (true or false)
- For reflexive verbs (e.g., 'se laver'), set "reflexive" to true
- Return ONLY valid JSON with no extra text, comments, or trailing commas

AUXILIARY DETERMINATION:
- CRITICAL SPECIAL CASES (these override all other rules):
  * The verb "être" ALWAYS uses the auxiliary "avoir" (passé composé: "j'ai été")
  * The verb "avoir" ALWAYS uses the auxiliary "avoir" (passé composé: "j'ai eu")
- DR MRS VANDERTRAMP verbs use "être": devenir, revenir, monter, rester, sortir, venir, arriver, naître, descendre, entrer, rentrer, tomber, retourner, aller, mourir, partir, passer
- All reflexive verbs use "être" (se laver, s'appeler, se lever, etc.)
- Most other verbs use "avoir" (manger, parler, savoir, pouvoir, faire, dire, etc.)
- When unsure, default to "avoir"

VERB GROUP CLASSIFICATION:
- first_group: ALL -er verbs except "aller" (parler, manger, aimer, donner, regarder, penser, appeler, jeter, etc.)
  Note: Stem-changing -er verbs like "appeler" (j'appelle) are STILL first_group
  Exception: Only "aller" is third_group despite -er ending
- second_group: Regular -ir verbs with -issant pattern (finir→finissant, choisir→choisissant, obéir→obéissant, réussir→réussissant, réfléchir→réfléchissant)
- third_group: All irregular verbs + irregular -ir/-oir/-re verbs (être, avoir, faire, voir, venir, prendre, mettre, dire, etc.)

CRITICAL: "appeler", "jeter", and other stem-changing -er verbs are first_group, NOT third_group!

KEY PATTERNS:
- If verb ends in -er AND is regular → first_group (except "aller")
- If verb ends in -ir AND present participle is -issant → second_group
- If verb is irregular OR ends in -oir/-re → third_group
- If verb ends in -ir but NOT -issant pattern → third_group (dormir, partir, sortir, servir, sentir, etc.)
"""

    def _get_conjugation_prompt(
        self, verb_infinitive: str, auxiliary: str, reflexive: bool
    ) -> str:
        """
        Generate prompt for extracting ONLY conjugations (no verb properties).

        Used when verb properties already exist in database and we only need tenses.
        The verb's auxiliary and reflexive status are provided from the database.
        """
        reflexive_note = " (reflexive verb)" if reflexive else ""

        return f"""
You are a French verb conjugation expert. Provide conjugations for the verb '{verb_infinitive}'{reflexive_note} with auxiliary '{auxiliary}'.

Tenses must be named exactly as follows:
- 'present'
- 'passe_compose'
- 'imparfait'
- 'future_simple'
- 'conditionnel'
- 'subjonctif'
- 'imperatif'

Return ONLY this JSON array (no other text):
[
    {{
        "infinitive": "{verb_infinitive}",
        "auxiliary": "{auxiliary}",
        "reflexive": {str(reflexive).lower()},
        "tense": "present",
        "first_person_singular": "",
        "second_person_singular": "",
        "third_person_singular": "",
        "first_person_plural": "",
        "second_person_plural": "",
        "third_person_plural": ""
    }},
    ...repeat for all 7 tenses...
]

CRITICAL RULES:
- Provide conjugations for ALL 7 tenses listed above
- Do NOT include the pronoun in the conjugations (e.g., "parle" not "je parle")
- The `infinitive`, `auxiliary`, and `reflexive` fields MUST be repeated for each tense
- Use EXACTLY the tense names listed above (no variations)
- For reflexive verbs, include the reflexive pronoun in conjugations (e.g., "me lave", "te laves")
- Return ONLY valid JSON array with no extra text, comments, or trailing commas
"""

    def _get_objects_prompt(self, verb_infinitive: str, auxiliary: str) -> str:
        return f"""
You are a French verb expert. Analyze the verb '{verb_infinitive}' with auxiliary '{auxiliary}'.

Return ONLY this JSON (no other text):
{{
    "can_have_cod": boolean,
    "can_have_coi": boolean
}}

DEFINITIONS:
- COD: Direct object with NO preposition → "verbe + quelque chose/quelqu'un"
- COI: Indirect object with preposition à/de → "verbe + à/de + quelque chose/quelqu'un"

CLASSIFICATION RULES:

=== COD ONLY ===
Pattern: verb + direct object (NO preposition)
Examples: manger (qqch), voir (qqn), prendre (qqch), faire (qqch), avoir (qqch), lire (qqch), boire (qqch), choisir (qqch), comprendre (qqch), entendre (qqch), perdre (qqch), trouver (qqch), suivre (qqn), regarder (qqch)

=== COI ONLY ===
Pattern: verb + à/de + object (REQUIRES preposition)
Examples:
- téléphoner à (qqn), répondre à (qqn), obéir à (qqn)
- appartenir à (qqn), plaire à (qqn), ressembler à (qqn)
- réfléchir à (qqch), réussir à (qqch), parvenir à (qqch)

CRITICAL: If verb ALWAYS requires à/de → COI ONLY

=== BOTH COD AND COI ===
Pattern: verb + COD + à/de + COI (ditransitive)
Common pattern: "verbe + quelque chose + à quelqu'un"
Examples:
- donner qqch à qqn, dire qqch à qqn, promettre qqch à qqn
- enseigner qqch à qqn, apprendre qqch à qqn, montrer qqch à qqn
- expliquer qqch à qqn, écrire qqch à qqn, offrir qqch à qqn
- demander qqch à qqn, permettre qqch à qqn, confier qqch à qqn
- lire qqch à qqn, devoir qqch à qqn  # ADD THESE

Special cases that allow both patterns:
- penser: "Je pense cela" (COD) OR "Je pense à toi" (COI)

=== NEITHER ===
Intransitive verbs (no objects at all)
Examples: aller, venir, arriver, partir, rester, naître, mourir, dormir, rire, sourire, tomber, devenir, bâiller, soupirer, courir

CRITICAL: These verbs CANNOT take COD or COI:
- Laughing/smiling verbs: rire, sourire, ricaner (NEVER "rire à quelqu'un")
- Body actions: bâiller, soupirer (NEVER take objects)
- Movement without destination: courir (intransitive - no object)
- Birth/death: naître, mourir (NEVER take objects)

=== COI ONLY ===
Pattern: verb + à/de + object (REQUIRES preposition)
Examples:
- téléphoner à (qqn), répondre à (qqn), obéir à (qqn)
- appartenir à (qqn), plaire à (qqn), ressembler à (qqn)
- réfléchir à (qqch), réussir à (qqch), parvenir à (qqch)

CRITICAL: These ONLY take COI, NEVER COD:
- répondre (ALWAYS "répondre à" - NEVER direct object)
- réussir (ALWAYS "réussir à" - NEVER direct object)
- obéir (ALWAYS "obéir à" - NEVER direct object)

=== REFLEXIVE VERBS ===
All reflexive verbs use "être" and the reflexive pronoun (se/me/te) IS the object.
They are classified as NEITHER (can_have_cod: false, can_have_coi: false)
Examples: se laver, s'habiller, s'arrêter, se lever, se coucher
Exception: se souvenir takes "de": "Je me souviens DE toi" → can_have_coi: true

AUXILIARY-SPECIFIC RULES:

When auxiliary is AVOIR (transitive):
- sortir → COD only: "J'ai sorti les poubelles"
- monter → COD only: "J'ai monté les valises"
- descendre → COD only: "J'ai descendu l'escalier"
- rentrer → COD only: "J'ai rentré la voiture"
- passer → COD only: "J'ai passé du temps"

When auxiliary is ÊTRE (intransitive):
- sortir → NEITHER: "Je suis sorti"
- monter → NEITHER: "Je suis monté"
- descendre → NEITHER: "Je suis descendu"
- rentrer → NEITHER: "Je suis rentré"
- passer → NEITHER: "Je suis passé"

ANALYSIS STEPS:
1. Check if verb is in the examples above → use that classification
2. If not in examples:
   a. Does verb REQUIRE à/de preposition? → COI ONLY
   b. Can verb take "quelque chose" directly? → Check for COD
   c. Can verb take "à/de quelqu'un/quelque chose"? → Check for COI
   d. Does verb fit "donner qqch à qqn" pattern? → BOTH
3. Consider auxiliary '{auxiliary}' for transitivity changes

REASONING GUARD RAILS:
- If verb is intransitive by nature → NEITHER (don't add COI just because "à" could theoretically fit)
- If verb is reflexive (has "se") → Usually NEITHER (the "se" is the object)
- Just because you CAN add "à quelqu'un" doesn't mean it's standard French
- Verify the pattern is COMMON usage, not theoretical possibility
"""

    def _get_verb_prompt(
        self,
        verb_infinitive: str,
        target_language_code: str = "eng",
        include_tenses: bool = True,
    ) -> str:
        tense_section = ""
        if include_tenses:
            tense_section = """
Tenses must be named exactly as follows:
- 'present'
- 'passe_compose'
- 'imparfait'
- 'future_simple'
- 'conditionnel'
- 'subjonctif'
- 'imperatif'
"""

        # When include_tenses=False, COMPLETELY OMIT the tenses field from the JSON
        # Don't even show an empty array - the LLM will try to fill it
        tenses_json = (
            """,

    "tenses": [
        {{
            "infinitive": "{verb_infinitive}",
            "auxiliary": "",
            "reflexive": boolean,
            "tense": "",
            "first_person_singular": "",
            "second_person_singular": "",
            "third_person_singular": "",
            "first_person_plural": "",
            "second_person_plural": "",
            "third_person_plural": ""
        }}
    ]"""
            if include_tenses
            else ""
        )

        tense_guidelines = (
            """
- Provide conjugations for all tenses listed above.
- Do not include the pronoun in the conjugations themselves.
- The `infinitive`, `auxiliary`, and `reflexive` fields MUST be repeated for each object in the `tenses` array."""
            if include_tenses
            else ""
        )

        return f"""
You are a French verb conjugation expert. Your task is to provide a complete and valid JSON object representing the verb '{verb_infinitive}'.
{tense_section}
The JSON structure MUST be as follows. Do not deviate.

{{
    "infinitive": "{verb_infinitive}",
    "target_language_code": "{target_language_code}",
    "auxiliary": "avoir",
    "reflexive": false,
    "translation": "English translation",
    "past_participle": "past participle form",
    "present_participle": "present participle form",
    "classification": "first_group",
    "is_irregular": false{tenses_json}
}}

CRITICAL RULES:
- The "auxiliary" field is REQUIRED and MUST be EXACTLY either "avoir" or "être" - NEVER leave it empty
- The "classification" field is REQUIRED and MUST be EXACTLY one of: "first_group", "second_group", or "third_group"
- The "reflexive" field is REQUIRED and MUST be a boolean (true or false)
- For reflexive verbs (e.g., 'se laver'), set "reflexive" to true{tense_guidelines}
- Return ONLY valid JSON with no extra text, comments, or trailing commas

AUXILIARY DETERMINATION:
- CRITICAL SPECIAL CASES (these override all other rules):
  * The verb "être" ALWAYS uses the auxiliary "avoir" (passé composé: "j'ai été")
  * The verb "avoir" ALWAYS uses the auxiliary "avoir" (passé composé: "j'ai eu")
- DR MRS VANDERTRAMP verbs use "être": devenir, revenir, monter, rester, sortir, venir, arriver, naître, descendre, entrer, rentrer, tomber, retourner, aller, mourir, partir, passer
- All reflexive verbs use "être" (se laver, s'appeler, se lever, etc.)
- Most other verbs use "avoir" (manger, parler, savoir, pouvoir, faire, dire, etc.)
- When unsure, default to "avoir"

VERB GROUP CLASSIFICATION:
- first_group: ALL -er verbs except "aller" (parler, manger, aimer, donner, regarder, penser, appeler, jeter, etc.)
  Note: Stem-changing -er verbs like "appeler" (j'appelle) are STILL first_group
  Exception: Only "aller" is third_group despite -er ending
- second_group: Regular -ir verbs with -issant pattern (finir→finissant, choisir→choisissant, obéir→obéissant, réussir→réussissant, réfléchir→réfléchissant)
- third_group: All irregular verbs + irregular -ir/-oir/-re verbs (être, avoir, faire, voir, venir, prendre, mettre, dire, etc.)

CRITICAL: "appeler", "jeter", and other stem-changing -er verbs are first_group, NOT third_group!

KEY PATTERNS:
- If verb ends in -er AND is regular → first_group (except "aller")
- If verb ends in -ir AND present participle is -issant → second_group
- If verb is irregular OR ends in -oir/-re → third_group
- If verb ends in -ir but NOT -issant pattern → third_group (dormir, partir, sortir, servir, sentir, etc.)
"""

    def generate_objects_prompt(self, verb_infinitive: str, auxiliary: str) -> str:
        """Generate prompt for determining COD/COI capabilities."""
        return self._get_objects_prompt(verb_infinitive, auxiliary)

    def generate_verb_properties_prompt(
        self, verb_infinitive: str, target_language_code: str = "eng"
    ) -> str:
        """
        Generate prompt for extracting essential verb properties only.

        DEPRECATED for normal use - verbs should be added via migrations.
        Kept for emergency tooling or special cases.
        """
        return self._get_verb_properties_prompt(verb_infinitive, target_language_code)

    def generate_conjugation_prompt(
        self, verb_infinitive: str, auxiliary: str, reflexive: bool
    ) -> str:
        """Generate prompt for extracting conjugations only (when verb properties already exist)."""
        return self._get_conjugation_prompt(verb_infinitive, auxiliary, reflexive)

    def generate_verb_prompt(
        self,
        verb_infinitive: str,
        target_language_code: str = "eng",
        include_tenses: bool = True,
    ) -> str:
        """
        DEPRECATED: Generate combined prompt for verb properties + conjugations.

        This method is kept for backward compatibility with the deprecated download_verb().
        New code should use:
        - generate_verb_properties_prompt() for properties only
        - generate_conjugation_prompt() for conjugations only
        - generate_objects_prompt() for COD/COI only
        """
        # For backward compatibility, still support the old combined prompt
        # but log a warning
        import logging

        logging.getLogger(__name__).warning(
            "generate_verb_prompt() is deprecated. Use generate_conjugation_prompt() instead."
        )

        # Return the old combined prompt for backward compatibility
        return self._get_verb_properties_prompt(verb_infinitive, target_language_code)
