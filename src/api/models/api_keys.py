"""
API Keys request and response models.

These models define the API contracts for API key management endpoints,
providing clean separation from internal service schemas.
"""

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyUpdateRequest(BaseModel):
    """
    Request model for updating an API key.

    All fields are optional for partial updates. Only provided fields
    will be updated, others remain unchanged.

    **Security Note**: Updating permissions requires admin privileges.
    """

    name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Human-readable name for the API key",
        json_schema_extra={
            "example": "Production Web App Key",
            "pattern": "^[a-zA-Z0-9\\s\\-_]+$",
        },
    )
    description: str | None = Field(
        None,
        max_length=500,
        description="Optional description explaining the key's purpose and usage",
        json_schema_extra={
            "example": "API key for the main production web application. Used for user-facing features including verb lookup and sentence generation."
        },
    )
    client_name: str | None = Field(
        None,
        max_length=100,
        description="Name of the client application using this key",
        json_schema_extra={
            "example": "Language Learning Web App",
            "pattern": "^[a-zA-Z0-9\\s\\-_]+$",
        },
    )
    permissions_scope: list[str] | None = Field(
        None,
        description="List of permissions granted to this API key",
        json_schema_extra={
            "example": ["read", "write"],
            "enum_values": ["read", "write", "admin"],
            "description": "Available permissions: 'read' (GET endpoints), 'write' (POST/PUT endpoints), 'admin' (management operations)",
        },
    )
    is_active: bool | None = Field(
        None,
        description="Whether the API key is active and can be used for authentication",
        json_schema_extra={"example": True},
    )
    rate_limit_rpm: int | None = Field(
        None,
        ge=1,
        le=10000,
        description="Rate limit in requests per minute (1-10000)",
        json_schema_extra={"example": 1000, "minimum": 1, "maximum": 10000},
    )
    allowed_ips: list[str] | None = Field(
        None,
        description="List of allowed IP addresses or CIDR blocks. Empty list allows all IPs.",
        json_schema_extra={
            "example": ["192.168.1.0/24", "10.0.0.1"],
            "description": "Supports individual IPs (e.g., '192.168.1.1') or CIDR notation (e.g., '192.168.1.0/24')",
        },
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Production Web App Key",
                "description": "API key for the main production web application",
                "client_name": "Language Learning Web App",
                "permissions_scope": ["read", "write"],
                "is_active": True,
                "rate_limit_rpm": 1000,
                "allowed_ips": ["192.168.1.0/24"],
            },
            "partial_update_example": {
                "name": "Updated Key Name",
                "rate_limit_rpm": 2000,
            },
        }
    )
