from fastapi import APIRouter, HTTPException, Depends
from app.models import LoginRequest, LoginResponse, User
from app.utils import supabase
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login with email/username and password"""
    email = request.email
    password = request.password

    # Support login with username via identifier
    if not email and request.identifier:
        if "@" in request.identifier:
            email = request.identifier
        else:
            # Resolve email via username
            result = supabase.table("admins").select("email").eq("username", request.identifier).execute()
            if not result.data:
                raise HTTPException(status_code=400, detail="invalid_username")
            email = result.data[0]["email"]

    if not email or not password:
        raise HTTPException(status_code=400, detail="email_or_username_and_password_required")

    # Authenticate with Supabase
    try:
        auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})

        if not auth_response or not auth_response.session:
            raise HTTPException(status_code=400, detail="login_failed")

        return LoginResponse(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            user=User(id=auth_response.user.id, email=auth_response.user.email)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current authenticated user"""
    if not user:
        raise HTTPException(status_code=401, detail="unauthorized")

    # Check if admin
    result = supabase.table("admins").select("user_id").eq("user_id", user.id).execute()
    is_admin = len(result.data) > 0

    return {"user": user, "isAdmin": is_admin}
