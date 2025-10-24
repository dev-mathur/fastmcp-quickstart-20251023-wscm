from typing import Optional
from config import Settings
from freelancer import Freelancer

def _get_client() -> Freelancer:
    s = Settings()  # call-time: sees .env locally or real env in Cloud
    print(f"[env] use_sandbox={s.use_sandbox} base={s.base_url} token_present={bool(s.token)} auth_style={s.auth_style}")
    if not s.token:
        raise ValueError("Missing FREELANCER_TOKEN or FREELANCER_SANDBOX_TOKEN")
    return Freelancer(token=s.token, base_url=s.base_url, auth_style=s.auth_style)

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