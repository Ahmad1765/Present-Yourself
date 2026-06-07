from fastapi import APIRouter, Depends, HTTPException, status

from app.adapters import get_storage
from app.auth import CurrentUser, get_current_user
from app.config import get_settings
from app.schemas.api import UploadSignIn, UploadSignOut

router = APIRouter(prefix="/uploads", tags=["uploads"])

_ALLOWED_TYPES = {
    "template": {"application/vnd.openxmlformats-officedocument.presentationml.presentation"},
    "image": {"image/jpeg", "image/png", "image/webp"},
}


@router.post("/sign", response_model=UploadSignOut)
async def sign_upload(
    payload: UploadSignIn,
    user: CurrentUser = Depends(get_current_user),
) -> UploadSignOut:
    settings = get_settings()
    allowed = _ALLOWED_TYPES.get(payload.purpose, set())
    if payload.content_type not in allowed:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Content type not allowed for this purpose")

    if payload.purpose == "template" and payload.size > settings.max_pptx_upload_mb * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large")
    if payload.purpose == "image" and payload.size > settings.max_image_upload_mb * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large")

    storage = get_storage()
    if payload.purpose == "template":
        ext = "pptx"
    else:
        # Derive image extension from validated content_type (already in _ALLOWED_TYPES)
        if not isinstance(payload.content_type, str) or "/" not in payload.content_type:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid content_type")
        subtype = payload.content_type.split("/", 1)[1].strip().lower()
        ext_map = {"jpeg": "jpg", "png": "png", "webp": "webp"}
        if subtype not in ext_map:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported image content_type")
        ext = ext_map[subtype]
    prefix = f"{payload.purpose}s/{user.id}"
    key = storage.new_key(prefix, ext)
    url = storage.presign_put(key, payload.content_type, expires=900)
    return UploadSignOut(upload_url=url, storage_key=key, expires_in=900)
