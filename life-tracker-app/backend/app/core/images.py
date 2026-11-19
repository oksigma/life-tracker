"""Photo processing: validate, rotate upright, strip all metadata, resize, re-encode as JPEG."""

from dataclasses import dataclass
from io import BytesIO

import pillow_heif
from PIL import Image, ImageOps, UnidentifiedImageError

pillow_heif.register_heif_opener()

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
FULL_SIZE_PX = 2000
THUMBNAIL_PX = 400
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "HEIF"}


class InvalidImageError(Exception):
    """The upload is not an image in a supported format."""


@dataclass(frozen=True)
class ProcessedPhoto:
    full: bytes
    thumbnail: bytes


def process_photo(data: bytes) -> ProcessedPhoto:
    """CPU-bound; call from a worker thread. Raises InvalidImageError for unusable uploads.

    The output JPEGs are encoded from pixel data only, so no EXIF (GPS location, camera,
    timestamps) or other metadata from the original survives.
    """
    try:
        with Image.open(BytesIO(data)) as original:
            if original.format not in ALLOWED_FORMATS:
                raise InvalidImageError(f"Unsupported image format: {original.format}")
            upright = ImageOps.exif_transpose(original)
            image = _to_rgb(upright)
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as exc:
        if isinstance(exc, InvalidImageError):
            raise
        raise InvalidImageError("File is not a readable image") from exc

    return ProcessedPhoto(
        full=_encode_jpeg(image, FULL_SIZE_PX, quality=85),
        thumbnail=_encode_jpeg(image, THUMBNAIL_PX, quality=80),
    )


def _to_rgb(image: Image.Image) -> Image.Image:
    """JPEG has no transparency: flatten any alpha channel onto white."""
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")


def _encode_jpeg(image: Image.Image, max_px: int, quality: int) -> bytes:
    resized = image.copy()
    resized.thumbnail((max_px, max_px), Image.Resampling.LANCZOS)
    # Pixel data only: don't pass exif/icc_profile, so no metadata is written.
    resized.info = {}
    buffer = BytesIO()
    resized.save(buffer, format="JPEG", quality=quality, optimize=True)
    return buffer.getvalue()
