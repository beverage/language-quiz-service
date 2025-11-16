"""Error types for sentence generation."""

from enum import Enum


class ErrorType(str, Enum):
    """Types of grammatical errors for incorrect sentences."""

    # COD_PRONOUN_ERROR = "cod_pronoun_error"  # Commented out for now
    # COI_PRONOUN_ERROR = "coi_pronoun_error"  # Commented out for now
    WRONG_CONJUGATION = "wrong_conjugation"
    WRONG_AUXILIARY = "wrong_auxiliary"
    # PAST_PARTICIPLE_AGREEMENT = "past_participle_agreement"  # Commented out for now
