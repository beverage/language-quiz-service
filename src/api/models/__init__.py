"""
API request and response models.

This module contains Pydantic models specifically designed for API contracts,
separate from internal service/domain schemas.
"""

from .api_keys import ApiKeyUpdateRequest
from .problems import (
    ProblemRandomRequest,
    ProblemResponse,
    ProblemStatementResponse,
)
from .sentences import SentenceGenerateRequest, SentenceListRequest, SentenceResponse
from .verbs import VerbDownloadRequest, VerbResponse, VerbWithConjugationsResponse

__all__ = [
    # API Keys
    "ApiKeyUpdateRequest",
    # Problems
    "ProblemRandomRequest",
    "ProblemResponse",
    "ProblemStatementResponse",
    # Sentences
    "SentenceGenerateRequest",
    "SentenceListRequest",
    "SentenceResponse",
    # Verbs
    "VerbDownloadRequest",
    "VerbResponse",
    "VerbWithConjugationsResponse",
]
