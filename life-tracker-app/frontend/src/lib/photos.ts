export const MAX_PHOTO_BYTES = 15 * 1024 * 1024;
export const ACCEPTED_PHOTO_TYPES = "image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif";

const ACCEPTED_MIME = ["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"];
const ACCEPTED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"];

/** Client-side check before uploading; the backend validates again. */
export function photoError(file: File): string | null {
  const name = file.name.toLowerCase();
  const typeOk = ACCEPTED_MIME.includes(file.type) || ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext));
  if (!typeOk) return "Choose a JPEG, PNG, WebP or HEIC photo.";
  if (file.size > MAX_PHOTO_BYTES) return "Photo must be 15 MB or smaller.";
  return null;
}
