from fastapi import APIRouter
from ..config import settings

router = APIRouter()

@router.get("/health")
async def health():
    return {"ok": True, "sandbox": settings.use_sandbox}