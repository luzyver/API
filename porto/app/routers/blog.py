from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import re
from app.models import BlogPost, User
from app.utils import supabase
from app.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/blog", tags=["blog"])


def generate_slug(title: str) -> str:
    """Generate URL-friendly slug from title"""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = slug.replace(' ', '-')
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


@router.get("")
async def get_blog_posts(
    q: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    limit: int = Query(12, le=50),
    offset: int = Query(0, ge=0),
    user: Optional[User] = Depends(get_current_user)
):
    """Get blog posts (public shows published only, admin shows all)"""
    # Check if user is admin
    is_admin = False
    if user:
        admin_result = supabase.table("admins").select("user_id").eq("user_id", user.id).execute()
        is_admin = len(admin_result.data) > 0

    query = supabase.table("blog_posts").select(
        "id,title,slug,excerpt,featured_image,tags,published,created_at,updated_at",
        count="exact"
    ).order("created_at", desc=True)

    # Only filter by published if not admin
    if not is_admin:
        query = query.eq("published", True)

    if q:
        query = query.or_(f"title.ilike.%{q}%,excerpt.ilike.%{q}%,content.ilike.%{q}%")

    if tag:
        query = query.contains("tags", [tag])

    query = query.range(offset, offset + limit - 1)
    result = query.execute()

    return {"items": result.data, "total": result.count}


@router.get("/posts")
async def get_blog_posts_admin(
    q: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_admin)
):
    """Get all blog posts (admin only)"""
    query = supabase.table("blog_posts").select("*", count="exact").order("created_at", desc=True)

    if q:
        query = query.or_(f"title.ilike.%{q}%,excerpt.ilike.%{q}%,content.ilike.%{q}%")

    query = query.range(offset, offset + limit - 1)
    result = query.execute()

    return {"items": result.data, "total": result.count}


@router.get("/{slug}")
async def get_blog_post(slug: str, user: Optional[User] = Depends(get_current_user)):
    """Get single blog post by slug (public for published, admin for all)"""
    # Check if user is admin
    is_admin = False
    if user:
        admin_result = supabase.table("admins").select("user_id").eq("user_id", user.id).execute()
        is_admin = len(admin_result.data) > 0

    query = supabase.table("blog_posts").select("*").eq("slug", slug)
    if not is_admin:
        query = query.eq("published", True)

    result = query.execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="post_not_found")

    return result.data[0]


@router.post("/posts")
async def create_blog_post(post: BlogPost, user: User = Depends(require_admin)):
    """Create new blog post (admin only)"""
    post_data = post.dict(exclude_none=True)

    # Generate slug if not provided
    if not post_data.get("slug") and post_data.get("title"):
        post_data["slug"] = generate_slug(post_data["title"])

    result = supabase.table("blog_posts").insert(post_data).execute()
    if result.data:
        return result.data[0]
    raise HTTPException(status_code=500, detail="failed_to_create_blog_post")


@router.post("/update")
async def update_blog_post(data: dict, user: User = Depends(require_admin)):
    """Update blog post (admin only)"""
    post_id = data.get("id")
    if not post_id:
        raise HTTPException(status_code=400, detail="id_required")

    update_data = {k: v for k, v in data.items() if k != "id"}

    # Update slug if title changed and slug not explicitly set
    if update_data.get("title") and "slug" not in data:
        update_data["slug"] = generate_slug(update_data["title"])

    result = supabase.table("blog_posts").update(update_data).eq("id", post_id).execute()
    if result.data:
        return result.data[0]
    raise HTTPException(status_code=404, detail="blog_post_not_found")


@router.delete("/{post_id}")
async def delete_blog_post(post_id: str, user: User = Depends(require_admin)):
    """Delete blog post (admin only)"""
    supabase.table("blog_posts").delete().eq("id", post_id).execute()
    return {"ok": True}
