from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.models import Project, User
from app.utils import supabase
from app.dependencies import require_admin

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
async def get_projects(
    q: Optional[str] = Query(None),
    stack: Optional[str] = Query(None),
    limit: int = Query(24, le=100),
    offset: int = Query(0, ge=0)
):
    """Get list of projects with optional filtering"""
    query = supabase.table("projects").select("*", count="exact").order("created_at", desc=True)

    if q:
        query = query.or_(f"title.ilike.%{q}%,description.ilike.%{q}%")

    if stack:
        parts = [s.strip() for s in stack.split(",") if s.strip()]
        if parts:
            query = query.contains("stack", parts)

    query = query.range(offset, offset + limit - 1)
    result = query.execute()

    return {"items": result.data, "total": result.count}


@router.get("/featured")
async def get_featured_projects():
    """Get featured projects"""
    result = supabase.table("projects").select("*").eq("featured", True).order("created_at", desc=True).limit(6).execute()
    return result.data


@router.post("")
async def create_project(project: Project, user: User = Depends(require_admin)):
    """Create a new project (admin only)"""
    result = supabase.table("projects").insert(project.dict(exclude_none=True)).execute()
    if result.data:
        return result.data[0]
    raise HTTPException(status_code=500, detail="failed_to_create_project")


@router.post("/update")
async def update_project(data: dict, user: User = Depends(require_admin)):
    """Update an existing project (admin only)"""
    project_id = data.get("id")
    if not project_id:
        raise HTTPException(status_code=400, detail="id_required")

    update_data = {k: v for k, v in data.items() if k != "id"}
    result = supabase.table("projects").update(update_data).eq("id", project_id).execute()

    if result.data:
        return result.data[0]
    raise HTTPException(status_code=404, detail="project_not_found")


@router.delete("/{project_id}")
async def delete_project(project_id: str, user: User = Depends(require_admin)):
    """Delete a project (admin only)"""
    supabase.table("projects").delete().eq("id", project_id).execute()
    return {"ok": True}
