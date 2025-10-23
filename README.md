# Freelancer MCP (Sandbox)

FastAPI + MCP server exposing:
- /gigs/me
- /gigs/recent
- /mcp (FastMCP manifest)

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8080
```