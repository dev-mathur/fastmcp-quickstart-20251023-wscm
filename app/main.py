from fastapi import FastAPI
from .routes import health, gigs
from .mcp_manifest import router as mcp_router

app = FastAPI(title="Freelancer MCP Server")

app.include_router(health.router)
app.include_router(gigs.router)
app.include_router(mcp_router)