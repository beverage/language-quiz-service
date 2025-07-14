"""Problem management endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/problems", tags=["problems"])

# TODO: Implement problem endpoints after discussing CLI/API boundary
# - POST /problems/ - Create problem
# - GET /problems/random - Generate random problem
# - GET /problems/{problem_id} - Get problem by ID
# - GET /problems/ - List/search problems
