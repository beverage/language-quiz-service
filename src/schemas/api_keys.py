"""
API Key schemas for authentication and management.
"""

import secrets
import string
from typing import Tuple

from datetime import datetime
from typing import List, Optional
from uuid import UUID
import ipaddress

from pydantic import BaseModel, Field, field_validator


class ApiKeyCreate(BaseModel):
    """Schema for creating a new API key."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Human-readable name for the API key",
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Optional description"
    )
    client_name: Optional[str] = Field(
        None, max_length=100, description="Client application name"
    )
    permissions_scope: List[str] = Field(
        default=["read"], description="Permissions for this key"
    )
    rate_limit_rpm: int = Field(
        default=100, ge=1, le=10000, description="Requests per minute limit"
    )
    allowed_ips: Optional[List[str]] = Field(
        None, description="Optional IP allowlist (CIDR notation supported)"
    )

    @field_validator("permissions_scope")
    @classmethod
    def validate_permissions(cls, v):
        valid_permissions = {"read", "write", "admin"}
        for permission in v:
            if permission not in valid_permissions:
                raise ValueError(
                    f"Invalid permission: {permission}. Must be one of {valid_permissions}"
                )
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty or just whitespace")
        return v.strip()

    @field_validator("allowed_ips")
    @classmethod
    def validate_allowed_ips(cls, v):
        if v is not None:
            for ip in v:
                try:
                    ipaddress.ip_network(ip, strict=False)
                except ValueError:
                    raise ValueError(f"Invalid IP address or CIDR notation: {ip}")
        return v


class ApiKeyUpdate(BaseModel):
    """Schema for updating an existing API key."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    client_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    permissions_scope: Optional[List[str]] = None
    rate_limit_rpm: Optional[int] = Field(None, ge=1, le=10000)
    allowed_ips: Optional[List[str]] = Field(
        None, description="Optional IP allowlist (CIDR notation supported)"
    )

    @field_validator("permissions_scope")
    @classmethod
    def validate_permissions(cls, v):
        if v is not None:
            valid_permissions = {"read", "write", "admin"}
            for permission in v:
                if permission not in valid_permissions:
                    raise ValueError(
                        f"Invalid permission: {permission}. Must be one of {valid_permissions}"
                    )
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Name cannot be empty or just whitespace")
        return v.strip() if v else v

    @field_validator("allowed_ips")
    @classmethod
    def validate_allowed_ips(cls, v):
        if v is not None:
            for ip in v:
                try:
                    ipaddress.ip_network(ip, strict=False)
                except ValueError:
                    raise ValueError(f"Invalid IP address or CIDR notation: {ip}")
        return v


class ApiKey(BaseModel):
    """Complete API key model (internal use, includes sensitive data)."""

    id: UUID
    key_hash: str
    key_prefix: str
    name: str
    description: Optional[str] = None
    client_name: Optional[str] = None
    is_active: bool = True
    permissions_scope: List[str] = Field(default_factory=lambda: ["read"])
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    rate_limit_rpm: int = 100
    allowed_ips: Optional[List[str]] = None

    model_config = {
        "from_attributes": True
    }  # For Pydantic v2 compatibility with SQLAlchemy/DB models


class ApiKeyResponse(BaseModel):
    """Safe API key response (no sensitive data exposed)."""

    id: UUID
    key_prefix: str
    name: str
    description: Optional[str] = None
    client_name: Optional[str] = None
    is_active: bool
    permissions_scope: List[str]
    created_at: datetime
    last_used_at: Optional[datetime] = None
    usage_count: int
    rate_limit_rpm: int
    allowed_ips: Optional[List[str]] = None

    model_config = {"from_attributes": True}


class ApiKeyWithPlainText(BaseModel):
    """Response when creating a new API key - includes the plain text key."""

    api_key: str = Field(
        ..., description="The actual API key - save this, it won't be shown again!"
    )
    key_info: ApiKeyResponse = Field(..., description="API key metadata")

    model_config = {"from_attributes": True}


class ApiKeyStats(BaseModel):
    """API key usage statistics."""

    total_keys: int
    active_keys: int
    inactive_keys: int
    total_requests: int
    requests_last_24h: Optional[int] = None
    most_active_key: Optional[str] = None  # key_prefix


# Utility functions for key generation
def generate_api_key() -> Tuple[str, str]:
    """
    Generate a secure API key and its prefix.

    Returns:
        Tuple of (full_api_key, key_prefix)
    """
    # Generate a secure random key with 56 alphanumeric characters
    # Format: sk_live_[56 random chars] = 64 total length
    alphabet = string.ascii_letters + string.digits
    random_part = "".join(secrets.choice(alphabet) for _ in range(56))

    full_key = f"sk_live_{random_part}"
    key_prefix = full_key[:12]  # "sk_live_" + first 4 chars of random part

    return full_key, key_prefix


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for secure storage.

    Args:
        api_key: The plain text API key

    Returns:
        Hashed API key suitable for database storage
    """
    import bcrypt
    import os

    # Use faster rounds for testing, secure rounds for production
    rounds = 4 if os.getenv("ENVIRONMENT") == "test" else 12
    salt = bcrypt.gensalt(rounds=rounds)
    key_hash = bcrypt.hashpw(api_key.encode("utf-8"), salt)

    return key_hash.decode("utf-8")


def verify_api_key(api_key: str, key_hash: str) -> bool:
    """
    Verify an API key against its hash.

    Args:
        api_key: The plain text API key to verify
        key_hash: The stored hash to verify against

    Returns:
        True if the key matches the hash
    """
    import bcrypt

    try:
        return bcrypt.checkpw(api_key.encode("utf-8"), key_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def check_ip_allowed(client_ip: str, allowed_ips: Optional[List[str]]) -> bool:
    """
    Check if a client IP is allowed based on the allowlist.

    Args:
        client_ip: The client's IP address
        allowed_ips: List of allowed IPs/CIDR ranges, or None for no restrictions

    Returns:
        True if IP is allowed or no restrictions, False otherwise
    """
    if not allowed_ips:
        return True  # No restrictions

    try:
        client_addr = ipaddress.ip_address(client_ip)
        for allowed_ip in allowed_ips:
            allowed_network = ipaddress.ip_network(allowed_ip, strict=False)
            if client_addr in allowed_network:
                return True
        return False
    except (ValueError, TypeError):
        return False  # Invalid IP format
