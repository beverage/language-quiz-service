"""
API Keys request and response models.
"""

from pydantic import BaseModel, Field


class ApiKeyUpdateRequest(BaseModel):
    """Request model for updating an API key."""

    name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Human-readable name for the API key",
    )
    description: str | None = Field(
        None, max_length=500, description="Optional description"
    )
    client_name: str | None = Field(
        None, max_length=100, description="Client application name"
    )
    permissions_scope: list[str] | None = Field(
        None, description="Permissions for this key"
    )
    is_active: bool | None = Field(
        None, description="Whether the API key is active"
    )
    rate_limit_rpm: int | None = Field(
        None, ge=1, le=10000, description="Rate limit in requests per minute"
    )
    allowed_ips: list[str] | None = Field(
        None, description="List of allowed IP addresses (CIDR notation supported)"
    ) 