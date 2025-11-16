"""Disabled prompt builders for future reference.

These error types are commented out while we focus on core error types:
- COD (direct object) pronoun errors
- COI (indirect object) pronoun errors
- Past participle agreement errors

They may be re-enabled once multi-clause sentences are implemented.
"""

# COD/COI errors require multi-clause sentences to be unambiguous
# Past participle agreement needs gender-unambiguous pronouns

# def build_cod_error_prompt(sentence, verb, conjugations):
#     """Build prompt for COD pronoun error."""
#     pass

# def build_coi_error_prompt(sentence, verb, conjugations):
#     """Build prompt for COI pronoun error."""
#     pass

# def build_past_participle_agreement_prompt(sentence, verb, conjugations):
#     """Build prompt for past participle agreement error."""
#     pass
