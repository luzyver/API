from fastapi import APIRouter, HTTPException, Depends
from app.models import Message, User
from app.utils import supabase
from app.dependencies import require_admin

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("")
async def get_messages(user: User = Depends(require_admin)):
    """Get all messages (admin only)"""
    result = supabase.table("messages").select("*").order("created_at", desc=True).execute()
    return result.data


@router.post("")
async def create_message(message: Message):
    """Create a new contact message (public)"""
    insert_data = {
        "name": message.name,
        "message": message.message
    }
    if message.email:
        insert_data["email"] = message.email

    result = supabase.table("messages").insert(insert_data).execute()
    if result.data:
        return result.data[0]
    raise HTTPException(status_code=500, detail="failed_to_create_message")


@router.patch("/{message_id}")
@router.post("/{message_id}")
async def update_message(message_id: int, data: dict, user: User = Depends(require_admin)):
    """Update a message (admin only)"""
    update_data = {}
    if "read" in data and isinstance(data["read"], bool):
        update_data["read"] = data["read"]

    if not update_data:
        raise HTTPException(status_code=400, detail="no_updatable_fields")

    result = supabase.table("messages").update(update_data).eq("id", message_id).execute()
    if result.data:
        return result.data[0]
    raise HTTPException(status_code=404, detail="message_not_found")


@router.delete("/{message_id}")
async def delete_message(message_id: int, user: User = Depends(require_admin)):
    """Delete a message (admin only)"""
    supabase.table("messages").delete().eq("id", message_id).execute()
    return {"ok": True}


@router.post("/reset")
async def reset_messages(user: User = Depends(require_admin)):
    """Reset all messages (admin only)"""
    try:
        # Try RPC first
        supabase.rpc("truncate_messages").execute()
    except:
        # Fallback: delete all rows
        supabase.table("messages").delete().neq("id", 0).execute()
        try:
            supabase.rpc("reset_messages_identity").execute()
        except:
            pass

    return {"ok": True}
