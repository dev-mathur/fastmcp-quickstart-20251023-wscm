from typing import Any, Dict, List, Optional
import httpx
from config import Settings 

settings = Settings()

class Freelancer:
    def __init__(self, token):
        self.base = settings.base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base}{path}"
        async with httpx.AsyncClient(timeout=30.0) as http:
            r = await http.get(url, headers=self.headers, params=params)
        data = r.json()
        if r.status_code != 200 or data.get("status") != "success":
            raise Exception(r.status_code, f"Freelancer API error: {data}")
        return data["result"]
    
    async def me(self) -> Dict[str, Any]:
        return await self._get("/users/0.1/self")

    async def recent_projects(
    self,
    limit: int = 25,
    query: Optional[str] = None,
    compact: bool = True,
    sort_field: str = "time_submitted",
    sort_order: str = "desc"
) -> List[Dict[str, Any]]:
        params = {
            "limit": min(limit, 50),
            "sort_field": sort_field,
            "sort_order": sort_order,
        }
        if compact:
            params["compact"] = "true"
        if query:
            params["query"] = query

        result = await self._get("/projects/0.1/projects/active", params=params)
        projects = result.get("projects", [])

        if sort_field.startswith("time_"):
            projects.sort(key=lambda p: p.get("time_updated") or p.get("time_submitted") or 0, reverse=sort_order == "desc")

        return projects[:limit]