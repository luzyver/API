from fastapi import Header, HTTPException, Depends
from typing import Optional
from app.utils import supabase
from app.models import User


async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[User]:
    """Extract user from Authorization header"""
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        return None

    token = authorization[7:]  # Remove "Bearer " prefix

    try:
        response = supabase.auth.get_user(token)
        if response and response.user:
            return User(id=response.user.id, email=response.user.email)
    except Exception:
        return None

    return None


async def require_admin(user: Optional[User] = Depends(get_current_user)):
    """Ensure user is an admin"""
    if not user:
        raise HTTPException(status_code=401, detail="unauthorized")

    # Check if user is admin
    try:
        result = supabase.table("admins").select("user_id").eq("user_id", user.id).execute()
        if not result.data:
            raise HTTPException(status_code=403, detail="forbidden")
    except Exception as e:
        raise HTTPException(status_code=403, detail="forbidden")

    return user
