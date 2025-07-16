# src/core/exceptions.py


class AppException(Exception):
    """
    Base class for all application-specific exceptions.
    Carries an HTTP status code, a user-facing message, and optional details.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        *,
        details: dict | list | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class NotFoundError(AppException):
    """Resource not found (404)."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(AppException):
    """
    Validation failed (400).
    Used to wrap Pydantic or business rule validation errors with field-level details.
    """

    def __init__(self, message: str = "Validation error", *, details: dict | list):
        super().__init__(message, status_code=400, details=details)


class RepositoryError(AppException):
    """
    Generic data-access failure (500).
    Raised when a repository layer operation fails.
    """

    def __init__(self, message: str = "Repository error"):
        super().__init__(message, status_code=500)


class ServiceError(AppException):
    """
    Generic business-logic failure (500).
    Raised when a service layer operation fails.
    """

    def __init__(self, message: str = "Service error", status_code: int = 500):
        super().__init__(message, status_code=status_code)


class ContentGenerationError(ServiceError):
    """
    LLM content generation failure (503).
    Raised when an AI service (e.g., OpenAI) fails to generate required content.
    """

    def __init__(
        self,
        message: str = "Content generation failed",
        *,
        content_type: str | None = None,
    ):
        full_message = f"AI ({content_type or 'general'}): {message}"
        super().__init__(full_message, status_code=503)


class LanguageResourceNotFoundError(NotFoundError):
    """
    A specific language resource (e.g., a verb in a specific language) was not found.
    Inherits from NotFoundError (404).
    """

    def __init__(
        self,
        message: str = "Language resource not found",
        *,
        resource_type: str | None = None,
    ):
        full_message = (
            f"Language resource ({resource_type or 'general'}) not found: {message}"
        )
        super().__init__(full_message)
