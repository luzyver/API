from fastapi import APIRouter, HTTPException, Depends, Query
from app.models import Experience, User
from app.utils import supabase
from app.dependencies import require_admin

router = APIRouter(prefix="/experiences", tags=["experiences"])


@router.get("")
async def get_experiences(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0)
):
    """Get all experiences (public)"""
    query = supabase.table("experiences").select("*", count="exact").order("start_date", desc=True)
    query = query.range(offset, offset + limit - 1)
    result = query.execute()
    return result.data


@router.post("")
async def create_experience(experience: Experience, user: User = Depends(require_admin)):
    """Create a new experience (admin only)"""
    result = supabase.table("experiences").insert(experience.dict(exclude_none=True)).execute()
    if result.data:
        return result.data[0]
    raise HTTPException(status_code=500, detail="failed_to_create_experience")


@router.post("/update")
async def update_experience(data: dict, user: User = Depends(require_admin)):
    """Update an experience (admin only)"""
    experience_id = data.get("id")
    if not experience_id:
        raise HTTPException(status_code=400, detail="id_required")

    update_data = {k: v for k, v in data.items() if k != "id"}
    result = supabase.table("experiences").update(update_data).eq("id", experience_id).execute()

    if result.data:
        return result.data[0]
    raise HTTPException(status_code=404, detail="experience_not_found")


@router.delete("/{experience_id}")
async def delete_experience(experience_id: str, user: User = Depends(require_admin)):
    """Delete an experience (admin only)"""
    supabase.table("experiences").delete().eq("id", experience_id).execute()
    return {"ok": True}
