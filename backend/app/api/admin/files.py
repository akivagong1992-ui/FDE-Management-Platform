import secrets
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.core.deps import get_current_user

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    _: dict = Depends(get_current_user),
) -> dict:
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.UPLOAD_MAX_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件超过 {settings.UPLOAD_MAX_MB} MB",
        )

    upload_dir = Path(settings.UPLOAD_DIR) / datetime.utcnow().strftime("%Y/%m/%d")
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "upload.bin").suffix
    saved_name = f"{secrets.token_hex(8)}{suffix}"
    saved_path = upload_dir / saved_name
    saved_path.write_bytes(content)

    return {
        "filename": file.filename,
        "saved_path": str(saved_path.relative_to(settings.UPLOAD_DIR)),
        "size_bytes": len(content),
        "content_type": file.content_type,
    }
