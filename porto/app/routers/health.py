from fastapi import APIRouter
import sys

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    """Health check endpoint"""
    return {"ok": True}


@router.get("/diag")
async def diag():
    """Diagnostic information"""
    from app.config import get_settings
    settings = get_settings()

    return {
        "python": sys.version,
        "env": {
            "SUPABASE_URL": bool(settings.supabase_url),
            "SUPABASE_SERVICE_ROLE": bool(settings.supabase_service_role),
        }
    }
