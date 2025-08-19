import imghdr
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, UploadFile
from pydantic import BaseModel

from src.runner.config import settings

media_api = APIRouter(tags=["Media"])


class UploadResult(BaseModel):
    url: str
    filename: str
    size: int


MAX_BYTES = 10 * 1024 * 1024


@media_api.post("/media", response_model=UploadResult)
async def upload_image(request: Request, file: UploadFile) -> UploadResult:
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Only images are allowed")

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image too large")

    kind = imghdr.what(None, data)
    if kind not in {"png", "jpeg", "gif", "webp"}:
        raise HTTPException(status_code=400, detail="Unsupported image format")

    ext = {"jpeg": "jpg"}.get(kind, kind)
    filename = f"{uuid4().hex}.{ext}"
    dest = settings.media_root / filename

    dest.write_bytes(data)

    url = request.url_for("media", path=filename)
    return UploadResult(url=str(url), filename=filename, size=len(data))
