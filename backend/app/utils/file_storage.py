import os
import secrets
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.core.config import settings

ALLOWED_SUBDIRS = {
    "products",
    "categories",
    "vendors",
    "reviews",
    "builder",
    "vendor_applications",
}

_PIL_FORMAT_EXT = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
_ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp",
}


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _validate_content_type(content_type: str) -> None:
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, f"Invalid image type '{content_type}'")


def _validate_size(size: int) -> None:
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size > max_bytes:
        raise HTTPException(400, f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB}MB.")


def _build_filename(subdir: str, ext: str) -> str:
    token = secrets.token_hex(8)
    return f"{subdir}_{token}{ext}"


def _strip_exif(img: Image.Image) -> Image.Image:
    """
    Return a new Image with no EXIF metadata. Rebuilds from pixel data.
    Preserves transparency for PNG/WebP by using the same mode.
    """
    if not settings.EXIF_STRIP_ON_UPLOAD:
        return img
    data = list(img.getdata())
    clean = Image.new(img.mode, img.size)
    clean.putdata(data)
    return clean


async def save_upload(
    file: UploadFile,
    subdir: str = "products",
    max_width: int = 1600,
    quality: int = 85,
) -> dict:
    if subdir not in ALLOWED_SUBDIRS:
        raise HTTPException(400, f"Invalid upload subdir. Allowed: {ALLOWED_SUBDIRS}")

    _validate_content_type(file.content_type or "")
    contents = await file.read()
    _validate_size(len(contents))

    try:
        img = Image.open(BytesIO(contents))
        img.load()
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(400, "File is not a valid image.")

    fmt = (img.format or "").upper()
    ext = _PIL_FORMAT_EXT.get(fmt)
    if not ext:
        raise HTTPException(400, f"Unsupported image format '{fmt}'. Use JPEG, PNG, or WebP.")

    # Strip EXIF
    img = _strip_exif(img)

    target_dir = Path(settings.UPLOAD_DIR) / subdir
    _ensure_dir(target_dir)
    filename = _build_filename(subdir, ext)
    filepath = target_dir / filename

    if img.mode in ("RGBA", "P") and ext == ".jpg":
        img = img.convert("RGB")
    if img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGB")

    if img.width > max_width:
        ratio = max_width / float(img.width)
        img = img.resize((max_width, int(float(img.height) * ratio)), Image.Resampling.LANCZOS)

    save_kwargs: dict = {"optimize": True}
    if ext == ".png":
        save_kwargs["format"] = "PNG"
    elif ext == ".webp":
        save_kwargs["format"] = "WEBP"
        save_kwargs["quality"] = quality
    else:
        save_kwargs["format"] = "JPEG"
        save_kwargs["quality"] = quality

    try:
        img.save(filepath, **save_kwargs)
    except Exception:
        raise HTTPException(400, "Could not process image.")

    url_path = f"/uploads/{subdir}/{filename}"
    return {
        "url": url_path,
        "filename": filename,
        "content_type": file.content_type,
        "size": os.path.getsize(filepath),
    }