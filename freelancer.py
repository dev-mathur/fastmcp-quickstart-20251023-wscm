from __future__ import annotations
from typing import Optional, Dict, Any, List, Literal
import asyncio
import requests
from json import JSONDecodeError

AuthStyle = Literal["bearer", "oauth", "api_key"]

class Freelancer:
    def __init__(self, token: str, base_url: str, auth_style: AuthStyle = "bearer"):
        self.token = token
        self.base_url = base_url
        self.auth_style = auth_style

    def _headers(self) -> Dict[str, str]:
        if self.auth_style == "bearer":
            headers = {"Authorization": f"Bearer {self.token}"}
            mode = "bearer"
        elif self.auth_style == "oauth":
            headers = {"Freelancer-OAuth-V1": self.token}
            mode = "oauth"
        else:  # "api_key"
            headers = {"Freelancer-API-Key": self.token}
            mode = "api_key"

        # Mimic python-requests defaults to avoid WAF heuristics that reject custom agents.
        headers.setdefault("Accept", "*/*")
        headers.setdefault("Accept-Encoding", "gzip, deflate")
        headers.setdefault("Connection", "keep-alive")
        headers["User-Agent"] = "python-requests/2.32.3"
        print(f"[freelancer] auth_mode={mode}")
        return headers

    async def recent_projects(
        self,
        limit: int = 10,
        query: Optional[str] = None,
        compact: bool = True,
        sort_field: str = "time_submitted",
        sort_order: str = "desc",
    ) -> List[dict]:
        params: Dict[str, Any] = {
            "limit": limit,
            "compact": "true" if compact else "false",
            "sort_field": sort_field,
            "sort_order": sort_order,
        }
        if query:
            params["query"] = query

        # Match your working script (no trailing slash)
        url = f"{self.base_url}/projects/0.1/projects/active"

        def _fetch() -> requests.Response:
            return requests.get(
                url,
                headers=self._headers(),
                params=params,
                timeout=20,
            )

        loop = asyncio.get_running_loop()
        resp = await loop.run_in_executor(None, _fetch)

        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            preview = resp.text[:300].replace("\n", " ")
            raise RuntimeError(f"API {resp.status_code} {resp.reason}; body: {preview}") from e
        except requests.RequestException as e:
            raise RuntimeError(f"Request failed: {e}") from e

        try:
            data = resp.json()
        except JSONDecodeError as e:
            preview = resp.text[:300].replace("\n", " ")
            ct = resp.headers.get("content-type", "")
            raise RuntimeError(f"API returned non-JSON (content-type: {ct}); body: {preview}") from e

        if isinstance(data, dict):
            data = data.get("result", {}).get("projects", [])
        return data or []
