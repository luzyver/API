from fastapi import APIRouter, Depends
from app.models import Stats, User
from app.utils import supabase
from app.dependencies import require_admin

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=Stats)
async def get_stats(user: User = Depends(require_admin)):
    """Get various statistics (admin only)"""
    stats = Stats()

    # Count projects
    result = supabase.table("projects").select("id", count="exact").execute()
    stats.projects = result.count or 0

    # Count images
    result = supabase.table("images").select("id", count="exact").execute()
    stats.images = result.count or 0

    # Count unread messages (null or false)
    result_null = supabase.table("messages").select("id", count="exact").is_("read", "null").execute()
    result_false = supabase.table("messages").select("id", count="exact").eq("read", False).execute()
    stats.unread = (result_null.count or 0) + (result_false.count or 0)

    # Count experiences
    result = supabase.table("experiences").select("id", count="exact").execute()
    stats.experiences = result.count or 0

    # Count comments
    result = supabase.table("comments").select("id", count="exact").execute()
    stats.comments = result.count or 0

    # Count blog posts
    result = supabase.table("blog_posts").select("id", count="exact").execute()
    stats.blog_posts = result.count or 0

    return stats
