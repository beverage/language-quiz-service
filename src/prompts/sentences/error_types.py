"""Error types for sentence generation."""

from enum import Enum


class ErrorType(str, Enum):
    """Types of grammatical errors for incorrect sentences.

    Organized by grammar focus area:
    - Conjugation focus: WRONG_CONJUGATION, WRONG_AUXILIARY
    - Pronouns focus: WRONG_PLACEMENT, WRONG_ORDER, WRONG_CATEGORY, WRONG_GENDER, WRONG_NUMBER
    """

    # Conjugation focus errors
    WRONG_CONJUGATION = "wrong_conjugation"
    WRONG_AUXILIARY = "wrong_auxiliary"

    # Pronouns focus errors
    WRONG_PLACEMENT = "wrong_placement"  # Pronoun in wrong position (after verb, outside negation, wrong clause)
    WRONG_ORDER = "wrong_order"  # Double pronouns in wrong sequence (e.g., *lui le instead of le lui)
    WRONG_CATEGORY = "wrong_category"  # COD used when COI needed or vice versa
    WRONG_GENDER = "wrong_gender"  # Wrong gender pronoun (detectable via être verb participle agreement)
    WRONG_NUMBER = "wrong_number"  # Wrong number (singular vs plural)
