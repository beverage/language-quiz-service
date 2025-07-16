"""Sentence management endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query

from src.api.models.sentences import SentenceResponse
from src.services.sentence_service import SentenceService

API_PREFIX = "/sentences"
router = APIRouter(prefix=API_PREFIX, tags=["sentences"])


async def get_sentence_service() -> SentenceService:
    """Dependency to get SentenceService instance."""
    return SentenceService()


@router.get("/random", response_model=SentenceResponse, summary="Get random sentence")
async def get_random_sentence(
    is_correct: Optional[bool] = Query(None, description="Filter by correctness"),
    verb_id: Optional[UUID] = Query(None, description="Filter by verb ID"),
    service: SentenceService = Depends(get_sentence_service),
) -> SentenceResponse:
    """
    Get a random sentence from the database.
    
    Optionally filter by correctness and/or verb ID.
    """
    try:
        sentence = await service.get_random_sentence(
            is_correct=is_correct,
            verb_id=verb_id,
        )
        
        if not sentence:
            raise HTTPException(status_code=404, detail="No sentences found matching criteria")
        
        # Convert service schema to API response model
        return SentenceResponse(**sentence.model_dump())
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get random sentence: {str(e)}")


@router.get("/{sentence_id}", response_model=SentenceResponse, summary="Get sentence by ID")
async def get_sentence(
    sentence_id: UUID,
    service: SentenceService = Depends(get_sentence_service),
) -> SentenceResponse:
    """Get a specific sentence by its ID."""
    try:
        sentence = await service.get_sentence(sentence_id)
        
        if not sentence:
            raise HTTPException(status_code=404, detail="Sentence not found")
        
        # Convert service schema to API response model
        return SentenceResponse(**sentence.model_dump())
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sentence: {str(e)}")


@router.get("/", response_model=List[SentenceResponse], summary="List sentences with filters")
async def list_sentences(
    verb_id: Optional[UUID] = Query(None, description="Filter by verb ID"),
    is_correct: Optional[bool] = Query(None, description="Filter by correctness"),
    tense: Optional[str] = Query(None, description="Filter by tense"),
    pronoun: Optional[str] = Query(None, description="Filter by pronoun"),
    target_language_code: Optional[str] = Query(None, description="Filter by target language"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    service: SentenceService = Depends(get_sentence_service),
) -> List[SentenceResponse]:
    """
    List sentences with optional filters.
    
    Supports filtering by verb, correctness, grammatical features, and language.
    """
    try:
        sentences = await service.get_sentences(
            verb_id=verb_id,
            is_correct=is_correct,
            tense=tense,
            pronoun=pronoun,
            target_language_code=target_language_code,
            limit=limit,
        )
        
        # Convert service schemas to API response models
        return [SentenceResponse(**sentence.model_dump()) for sentence in sentences]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sentences: {str(e)}")


@router.delete("/{sentence_id}", summary="Delete sentence")
async def delete_sentence(
    sentence_id: UUID,
    service: SentenceService = Depends(get_sentence_service),
) -> dict:
    """Delete a sentence."""
    try:
        deleted = await service.delete_sentence(sentence_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Sentence not found")
        
        return {"message": "Sentence deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete sentence: {str(e)}")