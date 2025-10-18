from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from app.models import Comment, User
from app.utils import supabase
from app.dependencies import require_admin
import asyncio
import json

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


@router.get("/stream")
async def stream_comments():
    """
    Server-Sent Events endpoint for realtime comments.
    Note: This is a basic polling implementation. For production,
    consider using Supabase Realtime directly from frontend or websockets.
    """
    async def event_generator():
        # Send initial connection message
        yield "event: connected\ndata: {}\n\n"

        last_id = 0
        try:
            # Get initial max ID
            result = supabase.table("comments").select("id").order("id", desc=True).limit(1).execute()
            if result.data and len(result.data) > 0:
                last_id = result.data[0]["id"]
        except:
            pass

        # Keep connection alive with heartbeat and check for new comments
        while True:
            try:
                # Send heartbeat
                yield ": keepalive\n\n"

                # Check for new comments
                result = supabase.table("comments").select("*").gt("id", last_id).order("id", desc=False).execute()

                if result.data:
                    for comment in result.data:
                        # Update last_id
                        if comment["id"] > last_id:
                            last_id = comment["id"]
                        # Send new comment as SSE event
                        yield f"data: {json.dumps(comment)}\n\n"

                # Wait before next poll (adjust interval as needed)
                await asyncio.sleep(2)

            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue streaming
                yield f": error: {str(e)}\n\n"
                await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
