"""
API Key management endpoints.
"""

import logging
import ipaddress
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPBearer

from src.api.models.api_keys import ApiKeyUpdateRequest
from src.core.auth import get_current_api_key, require_permission
from src.schemas.api_keys import (
    ApiKeyCreate,
    ApiKeyResponse,
    ApiKeyStats,
    ApiKeyUpdate,
    ApiKeyWithPlainText,
)
from src.services.api_key_service import ApiKeyService

logger = logging.getLogger(__name__)

API_PREFIX = "/api-keys"
ROUTER_PREFIX = f"/api/v1{API_PREFIX}"

router = APIRouter(prefix=API_PREFIX, tags=["api-keys"])
security = HTTPBearer()


@router.post(
    "/",
    response_model=ApiKeyWithPlainText,
    summary="Create a new API key",
    description="""
    Create a new API key with specified permissions and settings.

    **⚠️ Important**: The API key will only be shown once in the response.
    Save it securely as it cannot be retrieved again.

    **Permission Levels**:
    - `read`: Access to GET endpoints
    - `write`: Access to POST/PUT endpoints + read permissions
    - `admin`: Full access including API key management

    **Required Permission**: `admin`
    """,
    responses={
        200: {
            "description": "API key created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "api_key": "sk_live_abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567",
                        "key_info": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "key_prefix": "sk_live_abc1",
                            "name": "My Application Key",
                            "description": "API key for my web application",
                            "client_name": "Web App v1.0",
                            "is_active": True,
                            "permissions_scope": ["read", "write"],
                            "created_at": "2024-01-15T10:30:00Z",
                            "last_used_at": None,
                            "usage_count": 0,
                            "rate_limit_rpm": 1000,
                            "allowed_ips": ["192.168.1.0/24", "10.0.0.1"],
                        },
                    }
                }
            },
        },
        400: {
            "description": "Invalid request data",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Invalid permission: invalid_permission. Must be one of {'read', 'write', 'admin'}",
                        "status_code": 400,
                        "path": "/api-keys/",
                    }
                }
            },
        },
        403: {
            "description": "Insufficient permissions",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Admin permission required to create API keys",
                        "status_code": 403,
                        "path": "/api-keys/",
                    }
                }
            },
        },
    },
)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    request: Request,
    current_key: dict = Depends(get_current_api_key),
) -> ApiKeyWithPlainText:
    """
    Create a new API key.

    Requires 'admin' permission to create new keys.
    """
    # Check permissions
    permissions = current_key.get("permissions_scope", [])
    if "admin" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required to create API keys",
        )

    try:
        service = ApiKeyService()
        result = await service.create_api_key(api_key_data)

        logger.info(
            f"API key created: {result.key_info.name} by {current_key.get('name', 'unknown')}"
        )

        return result

    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key",
        )


@router.get(
    "/",
    response_model=list[ApiKeyResponse],
    summary="List all API keys",
    description="""
    Retrieve a list of all API keys in the system.

    **Filtering Options**:
    - `limit`: Maximum number of keys to return (default: 100)
    - `include_inactive`: Whether to include deactivated keys (default: false)

    **Required Permission**: `admin`
    """,
    responses={
        200: {
            "description": "List of API keys retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "key_prefix": "sk_live_abc1",
                            "name": "Production API Key",
                            "description": "Main production key",
                            "client_name": "Web App v1.0",
                            "is_active": True,
                            "permissions_scope": ["read", "write"],
                            "created_at": "2024-01-15T10:30:00Z",
                            "last_used_at": "2024-01-15T16:45:00Z",
                            "usage_count": 1523,
                            "rate_limit_rpm": 1000,
                            "allowed_ips": None,
                        },
                        {
                            "id": "456e7890-e89b-12d3-a456-426614174111",
                            "key_prefix": "sk_live_def2",
                            "name": "Development Key",
                            "description": "For development and testing",
                            "client_name": "Dev Environment",
                            "is_active": True,
                            "permissions_scope": ["read"],
                            "created_at": "2024-01-14T09:15:00Z",
                            "last_used_at": "2024-01-15T12:30:00Z",
                            "usage_count": 89,
                            "rate_limit_rpm": 100,
                            "allowed_ips": ["127.0.0.1", "::1"],
                        },
                    ]
                }
            },
        },
        403: {
            "description": "Insufficient permissions",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Admin permission required to list API keys",
                        "status_code": 403,
                        "path": "/api-keys/",
                    }
                }
            },
        },
    },
)
async def list_api_keys(
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of keys to return"
    ),
    include_inactive: bool = Query(
        False, description="Include deactivated keys in results"
    ),
    current_key: dict = Depends(get_current_api_key),
) -> list[ApiKeyResponse]:
    """
    List all API keys.

    Requires 'admin' permission to view all keys.
    """
    # Check permissions
    permissions = current_key.get("permissions_scope", [])
    if "admin" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required to list API keys",
        )

    try:
        service = ApiKeyService()
        return await service.get_all_api_keys(limit, include_inactive)

    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys",
        )


@router.get(
    "/stats",
    response_model=ApiKeyStats,
    summary="Get API key usage statistics",
    description="""
    Retrieve system-wide API key usage statistics and metrics.

    **Returns**:
    - Total number of API keys (active and inactive)
    - Usage metrics and request counts
    - Most active API key information

    **Required Permission**: `admin`
    """,
    responses={
        200: {
            "description": "API key statistics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "total_keys": 15,
                        "active_keys": 12,
                        "inactive_keys": 3,
                        "total_requests": 45672,
                        "requests_last_24h": 1234,
                        "most_active_key": "sk_live_abc1",
                    }
                }
            },
        },
        403: {
            "description": "Insufficient permissions",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Admin permission required to view API key statistics",
                        "status_code": 403,
                        "path": "/api-keys/stats",
                    }
                }
            },
        },
    },
)
async def get_api_key_stats(
    current_key: dict = Depends(get_current_api_key),
) -> ApiKeyStats:
    """
    Get API key usage statistics.

    Requires 'admin' permission to view statistics.
    """
    # Check permissions
    permissions = current_key.get("permissions_scope", [])
    if "admin" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required to view API key statistics",
        )

    try:
        service = ApiKeyService()
        return await service.get_api_key_stats()

    except Exception as e:
        logger.error(f"Error getting API key stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get API key statistics",
        )


@router.get("/search")
async def search_api_keys(
    name: str,
    current_key: dict = Depends(get_current_api_key),
) -> list[ApiKeyResponse]:
    """
    Search API keys by name pattern.

    Requires 'admin' permission to search keys.
    """
    # Check permissions
    permissions = current_key.get("permissions_scope", [])
    if "admin" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required to search API keys",
        )

    try:
        service = ApiKeyService()
        return await service.find_api_keys_by_name(name)

    except Exception as e:
        logger.error(f"Error searching API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search API keys",
        )


@router.get(
    "/current",
    response_model=ApiKeyResponse,
    summary="Get current API key information",
    description="""
    Retrieve information about the currently authenticated API key.

    **Use Cases**:
    - Verify API key authentication is working
    - Check current permissions and rate limits
    - View usage statistics for your key
    - Useful for debugging and monitoring

    **Required Permission**: Any (authenticated user can view their own key info)
    """,
    responses={
        200: {
            "description": "Current API key information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "key_prefix": "sk_live_abc1",
                        "name": "My Application Key",
                        "description": "API key for my web application",
                        "client_name": "Web App v1.0",
                        "is_active": True,
                        "permissions_scope": ["read", "write"],
                        "created_at": "2024-01-15T10:30:00Z",
                        "last_used_at": "2024-01-15T16:45:00Z",
                        "usage_count": 1523,
                        "rate_limit_rpm": 1000,
                        "allowed_ips": ["192.168.1.0/24"],
                    }
                }
            },
        },
        401: {
            "description": "No valid API key provided",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Invalid or missing API key",
                        "status_code": 401,
                        "path": "/api-keys/current",
                    }
                }
            },
        },
    },
)
async def get_current_key_info(
    current_key: dict = Depends(get_current_api_key),
) -> ApiKeyResponse:
    """
    Get information about the current API key.

    Any authenticated user can view their own key info.
    """
    try:
        return ApiKeyResponse.model_validate(current_key)

    except Exception as e:
        logger.error(f"Error getting current key info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get current key information",
        )


@router.get("/{api_key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    api_key_id: UUID,
    current_key: dict = Depends(get_current_api_key),
) -> ApiKeyResponse:
    """
    Get a specific API key by ID.

    Requires 'admin' permission to view other keys.
    """
    # Check permissions
    permissions = current_key.get("permissions_scope", [])
    if "admin" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required to view API key details",
        )

    try:
        service = ApiKeyService()
        result = await service.get_api_key(api_key_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting API key {api_key_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get API key",
        )


@router.put("/{api_key_id}", response_model=ApiKeyResponse)
async def update_api_key(
    api_key_id: UUID,
    api_key_data: ApiKeyUpdateRequest,
    current_key: dict = Depends(get_current_api_key),
) -> ApiKeyResponse:
    """
    Update an API key.

    Requires 'admin' permission to update keys.
    """
    # Check permissions
    permissions = current_key.get("permissions_scope", [])
    if "admin" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required to update API keys",
        )

    try:
        service = ApiKeyService()
        
        # Convert API request model to service model
        service_update_data = ApiKeyUpdate(
            name=api_key_data.name,
            description=api_key_data.description,
            client_name=api_key_data.client_name,
            permissions_scope=api_key_data.permissions_scope,
            is_active=api_key_data.is_active,
            rate_limit_rpm=api_key_data.rate_limit_rpm,
            allowed_ips=api_key_data.allowed_ips,
        )
        
        result = await service.update_api_key(api_key_id, service_update_data)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
            )

        logger.info(
            f"API key updated: {result.name} by {current_key.get('name', 'unknown')}"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating API key {api_key_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update API key",
        )


@router.delete("/{api_key_id}")
async def revoke_api_key(
    api_key_id: UUID,
    current_key: dict = Depends(get_current_api_key),
) -> dict:
    """
    Revoke (deactivate) an API key.

    Requires 'admin' permission to revoke keys.
    """
    # Check permissions
    permissions = current_key.get("permissions_scope", [])
    if "admin" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required to revoke API keys",
        )

    # Prevent self-revocation
    if str(api_key_id) == current_key.get("id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke the API key you are currently using",
        )

    try:
        service = ApiKeyService()
        success = await service.revoke_api_key(api_key_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
            )

        logger.info(
            f"API key revoked: {api_key_id} by {current_key.get('name', 'unknown')}"
        )

        return {"message": "API key revoked successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking API key {api_key_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key",
        )


@router.post("/{api_key_id}/validate")
async def validate_api_key_format(
    api_key_plain: str,
    current_key: dict = Depends(get_current_api_key),
) -> dict:
    """
    Validate an API key format without authenticating it.

    Requires 'admin' permission to validate keys.
    """
    # Check permissions
    permissions = current_key.get("permissions_scope", [])
    if "admin" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required to validate API keys",
        )

    try:
        service = ApiKeyService()
        is_valid, error_message = await service.verify_api_key_format(api_key_plain)

        return {
            "is_valid": is_valid,
            "error_message": error_message,
        }

    except Exception as e:
        logger.error(f"Error validating API key format: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate API key format",
        )
