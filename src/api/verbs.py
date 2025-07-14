"""Verb management endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/verbs", tags=["verbs"])

# TODO: Implement verb endpoints after discussing CLI/API boundary
# - POST /verbs/download - Download verb from AI
# - GET /verbs/random - Get random verb
# - GET /verbs/{verb_id} - Get verb by ID
# - GET /verbs/ - List/search verbs
# - GET /verbs/{verb_id}/conjugations - Get verb conjugations
