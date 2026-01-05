"""
API Key management endpoints.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPBearer

from src.api.models.api_keys import ApiKeyUpdateRequest
from src.core.auth import get_current_api_key
from src.core.dependencies import get_api_key_service
from src.core.exceptions import (
    AppException,
    NotFoundError,
    RepositoryError,
    ServiceError,
)
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

router = APIRouter(prefix=API_PREFIX, tags=["API Keys"])
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
                        "api_key": "sk_live_***",
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
    service: ApiKeyService = Depends(get_api_key_service),
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
        result = await service.create_api_key(api_key_data)

        logger.info(
            f"API key created: {result.key_info.name} by {current_key.get('name', 'unknown')}"
        )

        return result

    except (RepositoryError, ServiceError) as e:
        logger.error(f"API error creating key: {e}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except AppException as e:
        logger.error(f"Unhandled application error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
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
    service: ApiKeyService = Depends(get_api_key_service),
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
        return await service.get_all_api_keys(limit, include_inactive)

    except (RepositoryError, ServiceError) as e:
        logger.error(f"API error listing keys: {e}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except AppException as e:
        logger.error(f"Unhandled application error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
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
    service: ApiKeyService = Depends(get_api_key_service),
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
        return await service.get_api_key_stats()
    except (RepositoryError, ServiceError) as e:
        logger.error(f"API error getting key stats: {e}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except AppException as e:
        logger.error(f"Unhandled application error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.get("/search")
async def search_api_keys(
    name: str,
    current_key: dict = Depends(get_current_api_key),
    service: ApiKeyService = Depends(get_api_key_service),
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
        return await service.find_api_keys_by_name(name)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (RepositoryError, ServiceError) as e:
        logger.error(f"API error searching keys: {e}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except AppException as e:
        logger.error(f"Unhandled application error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
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
    # The get_current_api_key dependency already handles auth and returns the key.
    # No further service call is needed here, just return the context-injected key.
    # We map it to the response model to ensure it conforms to the public schema.
    return ApiKeyResponse.model_validate(current_key)


@router.get("/{api_key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    api_key_id: UUID,
    current_key: dict = Depends(get_current_api_key),
    service: ApiKeyService = Depends(get_api_key_service),
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
        return await service.get_api_key(api_key_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (RepositoryError, ServiceError) as e:
        logger.error(f"API error getting key {api_key_id}: {e}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except AppException as e:
        logger.error(f"Unhandled application error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.put(
    "/{api_key_id}",
    response_model=ApiKeyResponse,
    summary="Update API key",
    description="""
    Update an existing API key's properties.

    **Partial Updates Supported**: Only provide the fields you want to update.
    All fields are optional, and unchanged fields will retain their current values.

    **Updatable Properties:**
    - **Name & Description**: Update human-readable identification
    - **Client Information**: Modify associated client application details
    - **Permissions**: Grant or revoke access levels (read/write/admin)
    - **Status**: Activate or deactivate the key
    - **Rate Limiting**: Adjust request limits (1-10,000 RPM)
    - **IP Restrictions**: Modify allowed IP addresses or CIDR blocks

    **Security Considerations:**
    - Permission changes take effect immediately
    - Deactivated keys cannot authenticate until reactivated
    - IP restrictions apply to all requests using the key
    - Rate limit changes affect ongoing usage patterns

    **Use Cases:**
    - Rotate permissions for security compliance
    - Adjust rate limits based on usage patterns
    - Update client information for better tracking
    - Implement IP-based access controls
    - Temporarily disable compromised keys

    **Required Permission**: `admin` (only administrators can modify API keys)
    """,
    responses={
        200: {
            "description": "API key updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "key_prefix": "sk_live_prod",
                        "name": "Updated Production Key",
                        "description": "Updated API key for production web application",
                        "client_name": "Language Learning Web App v2",
                        "is_active": True,
                        "permissions_scope": ["read", "write"],
                        "created_at": "2024-01-15T10:30:00Z",
                        "last_used_at": "2024-01-15T16:45:00Z",
                        "usage_count": 1250,
                        "rate_limit_rpm": 2000,
                        "allowed_ips": ["192.168.1.0/24", "10.0.0.0/8"],
                    }
                }
            },
        },
        400: {
            "description": "Invalid request data",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_permissions": {
                            "summary": "Invalid permission values",
                            "value": {
                                "error": True,
                                "message": "Invalid permission 'invalid_perm'. Valid permissions: read, write, admin",
                                "status_code": 400,
                                "path": "/api/v1/api-keys/123e4567-e89b-12d3-a456-426614174000",
                            },
                        },
                        "invalid_ip": {
                            "summary": "Invalid IP address format",
                            "value": {
                                "error": True,
                                "message": "Invalid IP address '999.999.999.999' in allowed_ips",
                                "status_code": 400,
                                "path": "/api/v1/api-keys/123e4567-e89b-12d3-a456-426614174000",
                            },
                        },
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
                        "message": "Admin permission required to update API keys",
                        "status_code": 403,
                        "path": "/api/v1/api-keys/123e4567-e89b-12d3-a456-426614174000",
                    }
                }
            },
        },
        404: {
            "description": "API key not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "API key not found",
                        "status_code": 404,
                        "path": "/api/v1/api-keys/123e4567-e89b-12d3-a456-426614174000",
                    }
                }
            },
        },
        422: {
            "description": "Request validation failed",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "message": "Request validation failed",
                        "status_code": 422,
                        "path": "/api/v1/api-keys/123e4567-e89b-12d3-a456-426614174000",
                        "details": [
                            {
                                "field": "rate_limit_rpm",
                                "message": "Input should be greater than or equal to 1",
                                "type": "greater_than_equal",
                            }
                        ],
                    }
                }
            },
        },
    },
)
async def update_api_key(
    api_key_id: UUID,
    api_key_data: ApiKeyUpdateRequest,
    current_key: dict = Depends(get_current_api_key),
    service: ApiKeyService = Depends(get_api_key_service),
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

    update_data = api_key_data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided",
        )

    try:
        update_schema = ApiKeyUpdate(**update_data)
        return await service.update_api_key(api_key_id, update_schema)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (RepositoryError, ServiceError) as e:
        logger.error(f"API error updating key {api_key_id}: {e}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except AppException as e:
        logger.error(f"Unhandled application error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.delete("/{api_key_id}")
async def revoke_api_key(
    api_key_id: UUID,
    current_key: dict = Depends(get_current_api_key),
    service: ApiKeyService = Depends(get_api_key_service),
) -> dict:
    """
    Revoke (deactivate) an API key.

    Requires 'admin' permission.
    """
    # Check permissions
    permissions = current_key.get("permissions_scope", [])
    if "admin" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required to revoke API keys",
        )

    try:
        success = await service.revoke_api_key(api_key_id)
        if not success:
            # This case might occur if the key was already deleted by another process
            # or if there was a database error handled by the repository.
            # We raise not found because from the client's perspective, the key is gone.
            raise NotFoundError(
                f"API key with ID {api_key_id} not found or could not be revoked."
            )

        logger.info(
            f"API key {api_key_id} revoked by {current_key.get('name', 'unknown')}"
        )
        return {"message": f"API key {api_key_id} has been revoked."}

    except NotFoundError as e:
        logger.warning(f"Attempt to revoke non-existent API key {api_key_id}: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (RepositoryError, ServiceError) as e:
        logger.error(f"API error revoking key {api_key_id}: {e}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except AppException as e:
        logger.error(f"Unhandled application error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )
