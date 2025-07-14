"""Sentence management endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/sentences", tags=["sentences"])

# TODO: Implement sentence endpoints after discussing CLI/API boundary
# - POST /sentences/ - Create sentence
# - GET /sentences/random - Generate random sentence
# - GET /sentences/{sentence_id} - Get sentence by ID
# - GET /sentences/ - List/search sentences
