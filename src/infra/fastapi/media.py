import io
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel

MEDIA_ROOT = Path("var/media")
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)


class UploadResult(BaseModel):
    url: str
    filename: str
    size: int


media_api = APIRouter(tags=["Media"])

MAX_BYTES = 10 * 1024 * 1024
ALLOWED_FORMATS = {"jpeg": "jpg", "png": "png", "gif": "gif", "webp": "webp"}


@media_api.post("/media", response_model=UploadResult)
async def upload_image_raw(request: Request) -> UploadResult:
    ctype = (request.headers.get("content-type") or "").split(";")[0].lower()
    if not ctype.startswith("image/"):
        raise HTTPException(
            status_code=415, detail="Content-Type must be image/*"
        ) from None

    data = await request.body()
    if not data:
        raise HTTPException(status_code=400, detail="Empty body") from None
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image too large") from None

    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
        kind = (img.format or "").lower()
    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400, detail="Body is not a valid image"
        ) from None

    ext = ALLOWED_FORMATS.get(kind)
    if not ext:
        raise HTTPException(
            status_code=400, detail="Unsupported image format"
        ) from None

    filename = f"{uuid4().hex}.{ext}"
    (MEDIA_ROOT / filename).write_bytes(data)

    base_url = str(request.base_url).rstrip("/")
    return UploadResult(
        url=f"{base_url}/media/{filename}",
        filename=filename,
        size=len(data),
    )
