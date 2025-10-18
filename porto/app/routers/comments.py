from fastapi import APIRouter, HTTPException, Depends, Query
from app.models import Comment, User
from app.utils import supabase
from app.dependencies import require_admin

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("")
async def get_comments(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0)
):
    """Get all comments (public)"""
    query = supabase.table("comments").select("*", count="exact").order("created_at", desc=True)
    query = query.range(offset, offset + limit - 1)
    result = query.execute()
    return result.data


@router.post("")
async def create_comment(comment: Comment):
    """Create a new comment (public)"""
    if not comment.message or not comment.message.strip():
        raise HTTPException(status_code=400, detail="message_required")

    insert_data = {"message": comment.message}
    if comment.author:
        insert_data["author"] = comment.author

    result = supabase.table("comments").insert(insert_data).execute()
    if result.data:
        return result.data[0]
    raise HTTPException(status_code=500, detail="failed_to_create_comment")


@router.delete("/{comment_id}")
async def delete_comment(comment_id: int, user: User = Depends(require_admin)):
    """Delete a comment (admin only)"""
    supabase.table("comments").delete().eq("id", comment_id).execute()
    return {"ok": True}


@router.post("/reset")
async def reset_comments(user: User = Depends(require_admin)):
    """Reset all comments (admin only)"""
    try:
        supabase.rpc("truncate_comments").execute()
    except:
        supabase.table("comments").delete().neq("id", 0).execute()
        try:
            supabase.rpc("reset_comments_identity").execute()
        except:
            pass
    return {"ok": True}
