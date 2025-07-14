"""
API Key management endpoints.
"""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer

from src.core.auth import get_current_api_key
from src.services.api_key_service import ApiKeyService
from src.schemas.api_keys import (
    ApiKeyCreate,
    ApiKeyUpdate,
    ApiKeyResponse,
    ApiKeyWithPlainText,
    ApiKeyStats,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["api-keys"])
security = HTTPBearer()


@router.post("/", response_model=ApiKeyWithPlainText)
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


@router.get("/", response_model=List[ApiKeyResponse])
async def list_api_keys(
    limit: int = 100,
    include_inactive: bool = False,
    current_key: dict = Depends(get_current_api_key),
) -> List[ApiKeyResponse]:
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


@router.get("/stats", response_model=ApiKeyStats)
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
) -> List[ApiKeyResponse]:
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


@router.get("/current", response_model=ApiKeyResponse)
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
    api_key_data: ApiKeyUpdate,
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
        result = await service.update_api_key(api_key_id, api_key_data)

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
