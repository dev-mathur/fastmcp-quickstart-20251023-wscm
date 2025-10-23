from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from ..config import settings
from ..clients.freelancer import FreelancerClient

router = APIRouter(prefix="/gigs", tags=["gigs"])

class ProjectBudget(BaseModel):
    minimum: float | None = None
    maximum: float | None = None
    currency: Dict[str, Any] | None = None

class Project(BaseModel):
    id: int
    title: str
    budget: ProjectBudget | None = None
    time_submitted: int | None = None
    time_updated: int | None = None
    preview_description: str | None = None
    url: str | None = None

class RecentProjectsResponse(BaseModel):
    sorted_by: str = "time_updated_desc"
    projects: List[Project] = Field(default_factory=list)

def _client() -> FreelancerClient:
    token = settings.token
    if not token:
        raise HTTPException(500, "Missing token.")
    return FreelancerClient(token)

@router.get("/me")
async def whoami():
    return await _client().me()

@router.get("/recent", response_model=RecentProjectsResponse)
async def recent_projects(
    limit: int = Query(10, ge=1, le=50),
    query: Optional[str] = Query(None),
    compact: bool = Query(True),
    sort_field: str = Query("time_submitted"),
    sort_order: str = Query("desc"),
):
    projects = await _client().recent_projects(limit=limit, query=query, compact=compact, sort_field=sort_field, sort_order=sort_order)
    return {"sorted_by": f"{sort_field}_{sort_order}", "projects": projects}
