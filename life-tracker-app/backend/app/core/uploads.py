from fastapi import HTTPException, UploadFile, status

from app.core.images import MAX_UPLOAD_BYTES

# Photos never change for a given entry, so browsers can cache them indefinitely.
PHOTO_CACHE_HEADERS = {"Cache-Control": "private, max-age=31536000, immutable"}


async def read_photo_upload(photo: UploadFile) -> bytes:
    """Read an uploaded photo, rejecting files over the size limit with 413."""
    data = await photo.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"Photo must be {MAX_UPLOAD_BYTES // (1024 * 1024)} MB or smaller",
        )
    return data


def unsupported_photo_error() -> HTTPException:
    return HTTPException(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Photo must be a JPEG, PNG, WebP or HEIC image"
    )
