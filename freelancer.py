# freelancer.py
from __future__ import annotations
from typing import Optional, Dict, Any
import json
from json import JSONDecodeError
import httpx

class Freelancer:
    def __init__(self, token: str, base_url: str):
        self.token = token
        self.base_url = base_url.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "fastmcp-acting-agency/0.1",
        }

    async def recent_projects(
        self,
        limit: int = 10,
        query: Optional[str] = None,
        compact: bool = True,
        sort_field: str = "time_submitted",
        sort_order: str = "desc",
    ) -> list[dict]:
        params: Dict[str, Any] = {
            "limit": limit,
            "compact": "true" if compact else "false",
            "sort_field": sort_field,
            "sort_order": sort_order,
        }
        if query:
            params["q"] = query

        url = f"{self.base_url}/projects/0.1/projects"  # adjust path if yours differs

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, headers=self._headers(), params=params)

        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            body_preview = resp.text[:300].replace("\n", " ")
            raise RuntimeError(
                f"API {resp.status_code} {resp.reason_phrase}; body: {body_preview}"
            ) from e

        try:
            data = resp.json()
        except JSONDecodeError as e:
            body_preview = resp.text[:300].replace("\n", " ")
            ct = resp.headers.get("content-type", "")
            raise RuntimeError(
                f"API returned non-JSON (content-type: {ct}); body: {body_preview}"
            ) from e

        return data if isinstance(data, list) else data.get("result", {}).get("projects", [])