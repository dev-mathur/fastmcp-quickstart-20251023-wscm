from typing import Optional
from config import Settings
from freelancer import Freelancer

print("🔍 gigs.py is being imported!")  # Keep this for now

settings = Settings()

def _get_client() -> Freelancer:
    """Get authenticated Freelancer client"""
    token = settings.token
    if not token:
        raise ValueError("Missing FREELANCER_TOKEN or FREELANCER_SANDBOX_TOKEN")
    return Freelancer(token)


def register_tools():
    """Register all gigs tools with the MCP server"""
    from main import mcp  # Import here instead of at top
    
    @mcp.tool()
    async def search_acting_gigs(
        limit: int = 10,
        query: Optional[str] = None,
        sort_field: str = "time_submitted",
        sort_order: str = "desc"
    ) -> dict:
        """
        Search for recent acting and performance gigs on Freelancer
        
        Args:
            limit: Number of gigs to return (1-50)
            query: Search terms (e.g., "voice acting", "film actor", "theater")
            sort_field: Field to sort by (time_submitted, time_updated)
            sort_order: Sort order (asc or desc)
        
        Returns:
            Dictionary containing sorted_by field and list of gigs
        """
        try:
            if limit < 1 or limit > 50:
                return {"error": "Limit must be between 1 and 50"}
            
            client = _get_client()
            projects = await client.recent_projects(
                limit=limit,
                query=query,
                compact=True,
                sort_field=sort_field,
                sort_order=sort_order
            )
            
            return {
                "sorted_by": f"{sort_field}_{sort_order}",
                "total_results": len(projects),
                "gigs": projects
            }
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Failed to fetch gigs: {str(e)}"}


# Auto-register when module is imported
register_tools()