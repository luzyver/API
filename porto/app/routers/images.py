from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Response
from fastapi.responses import StreamingResponse
from typing import Optional
import base64
import re
from app.models import User
from app.utils import supabase
from app.dependencies import require_admin

router = APIRouter(prefix="/images", tags=["images"])


@router.get("")
async def get_images(
    limit: int = Query(24, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_admin)
):
    """Get list of images (admin only)"""
    query = supabase.table("images").select("id,filename,mime_type,created_at", count="exact").order("created_at", desc=True)
    query = query.range(offset, offset + limit - 1)
    result = query.execute()
    return {"items": result.data, "total": result.count}


@router.post("")
async def upload_image(
    file: Optional[UploadFile] = File(None),
    data_uri: Optional[str] = None,
    filename: Optional[str] = None,
    mime_type: Optional[str] = None,
    user: User = Depends(require_admin)
):
    """Upload a new image (admin only)"""
    if file:
        # Handle file upload
        file_bytes = await file.read()
        filename = file.filename
        mime_type = file.content_type or "application/octet-stream"
        base64_data = base64.b64encode(file_bytes).decode()
        data_uri = f"data:{mime_type};base64,{base64_data}"
    elif data_uri:
        # Validate data URI
        if not re.match(r'^data:[^;]+;base64,', data_uri):
            raise HTTPException(status_code=400, detail="invalid_or_missing_data_uri")
    else:
        raise HTTPException(status_code=400, detail="no_file_or_data_uri_provided")

    insert_data = {"data_uri": data_uri}
    if filename:
        insert_data["filename"] = filename
    if mime_type:
        insert_data["mime_type"] = mime_type

    result = supabase.table("images").insert(insert_data).execute()
    if result.data:
        image_id = result.data[0]["id"]
        return {
            "id": image_id,
            "filename": result.data[0].get("filename"),
            "mime_type": result.data[0].get("mime_type"),
            "url": f"/porto/images/{image_id}"
        }
    raise HTTPException(status_code=500, detail="failed_to_upload_image")


@router.post("/upload-for-editor")
async def upload_image_for_editor(
    file: UploadFile = File(...),
    user: User = Depends(require_admin)
):
    """Upload image for CKEditor (admin only)"""
    file_bytes = await file.read()

    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    filename = file.filename or "editor-upload.jpg"
    mime_type = file.content_type or "image/jpeg"
    base64_data = base64.b64encode(file_bytes).decode()
    data_uri = f"data:{mime_type};base64,{base64_data}"

    result = supabase.table("images").insert({
        "filename": filename,
        "mime_type": mime_type,
        "data_uri": data_uri
    }).execute()

    if result.data:
        return {"url": f"/porto/images/{result.data[0]['id']}"}
    raise HTTPException(status_code=500, detail="Upload failed")


@router.get("/{image_id}")
async def get_image(image_id: str):
    """Get image by ID (public)"""
    result = supabase.table("images").select("data_uri,mime_type,filename").eq("id", image_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="not_found")

    image = result.data[0]
    data_uri = image["data_uri"]

    # Parse data URI
    match = re.match(r'^data:([^;]+);base64,(.*)$', data_uri)
    if not match:
        raise HTTPException(status_code=400, detail="corrupt_data_uri")

    content_type = match.group(1) or image.get("mime_type") or "application/octet-stream"
    base64_data = match.group(2)

    try:
        img_bytes = base64.b64decode(base64_data)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_base64_data")

    return Response(content=img_bytes, media_type=content_type, headers={
        "Cache-Control": "public, max-age=31536000, immutable"
    })


@router.patch("/{image_id}")
@router.post("/{image_id}")
async def update_image(image_id: str, data: dict, user: User = Depends(require_admin)):
    """Update image metadata (admin only)"""
    update_data = {}
    if "filename" in data:
        update_data["filename"] = data["filename"]
    if "mime_type" in data:
        update_data["mime_type"] = data["mime_type"]

    if not update_data:
        raise HTTPException(status_code=400, detail="no_updatable_fields")

    result = supabase.table("images").update(update_data).eq("id", image_id).execute()
    if result.data:
        return result.data[0]
    raise HTTPException(status_code=404, detail="image_not_found")


@router.delete("/{image_id}")
async def delete_image(image_id: str, user: User = Depends(require_admin)):
    """Delete an image (admin only)"""
    supabase.table("images").delete().eq("id", image_id).execute()
    return {"ok": True}
