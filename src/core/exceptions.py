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

    def __init__(self, message: str = "Service error"):
        super().__init__(message, status_code=500)


class LanguageResourceNotFoundError(AppException):
    """Raised when required language resources are not available for content generation."""

    def __init__(self, resource_type: str, message: str = None):
        self.resource_type = resource_type
        super().__init__(
            message=message
            or f"Required {resource_type} resources not available for content generation",
            status_code=422,  # Unprocessable Entity - request cannot be processed due to missing resources
        )


class ContentGenerationError(AppException):
    """Raised when AI content generation fails after valid input."""

    def __init__(self, content_type: str = "content", message: str = None):
        self.content_type = content_type
        super().__init__(
            message=message or f"Failed to generate content - {content_type}",
            status_code=503,  # Service Temporarily Unavailable - AI service issue
        )


class InsufficientResourcesError(AppException):
    """Raised when there are insufficient resources to fulfill the request parameters."""

    def __init__(self, resource_type: str, required: int, available: int):
        self.resource_type = resource_type
        self.required = required
        self.available = available
        super().__init__(
            message=f"Insufficient {resource_type}: need {required}, only {available} available",
            status_code=422,  # Unprocessable Entity - cannot fulfill request parameters
        )
