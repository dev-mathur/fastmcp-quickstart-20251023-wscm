from typing import Optional
from config import Settings
from freelancer import Freelancer

settings = Settings()

def _get_client() -> Freelancer:
    token = settings.token
    if not token:
        raise ValueError("Missing FREELANCER_TOKEN or FREELANCER_SANDBOX_TOKEN")

    # IMPORTANT: base must match the token type
    base = settings.base_url  # e.g., sandbox if USE_SANDBOX=true
    return Freelancer(token=token, base_url=base)

def register_tools(mcp):
    @mcp.tool(name="search_acting_gigs", description="Search recent acting/performance gigs on Freelancer")
    async def search_acting_gigs(
        limit: int = 10,
        query: Optional[str] = None,
        sort_field: str = "time_submitted",
        sort_order: str = "desc",
    ) -> dict:
        if limit < 1 or limit > 50:
            return {"error": "Limit must be between 1 and 50"}
        try:
            client = _get_client()
            projects = await client.recent_projects(
                limit=limit, query=query, compact=True,
                sort_field=sort_field, sort_order=sort_order
            )
            return {
                "sorted_by": f"{sort_field}_{sort_order}",
                "total_results": len(projects),
                "gigs": projects,
            }
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Failed to fetch gigs: {e}"}