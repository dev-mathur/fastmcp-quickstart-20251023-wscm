from fastapi import APIRouter

router = APIRouter()

@router.get("/mcp")
async def mcp_manifest():
    return {
        "tools": [
            {
                "name": "get_recent_projects",
                "description": "Fetch most recent active Freelancer gigs.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
                        "query": {"type": "string", "description": "Keyword, e.g. 'acting'"},
                        "compact": {"type": "boolean", "default": True}
                    }
                },
                "http": {"method": "GET", "path": "/gigs/recent"}
            },
            {
                "name": "whoami",
                "description": "Return the linked Freelancer profile for the current token.",
                "input_schema": {"type": "object", "properties": {}},
                "http": {"method": "GET", "path": "/gigs/me"}
            }
        ]
    }