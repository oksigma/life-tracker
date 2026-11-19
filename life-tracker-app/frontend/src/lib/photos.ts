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

/** Vercel functions accept request bodies up to 4.5 MB (ADR 0004); stay safely under it. */
export const MAX_UPLOAD_BYTES = 4 * 1024 * 1024;
const MAX_DIMENSION = 2000;

function canvasToJpeg(canvas: HTMLCanvasElement, quality: number): Promise<Blob | null> {
  return new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", quality));
}

/**
 * Shrink photos over the upload limit to a ≤ 2000 px JPEG in the browser. The backend resizes to
 * the same size anyway and strips metadata again. Small photos are sent unchanged.
 */
export async function prepareForUpload(file: File): Promise<File> {
  if (file.size <= MAX_UPLOAD_BYTES) return file;
  let bitmap: ImageBitmap;
  try {
    bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
  } catch {
    throw new Error("This photo is too large to upload (over 4 MB) and can't be shrunk in this browser. Try a JPEG.");
  }
  const scale = Math.min(1, MAX_DIMENSION / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  canvas.getContext("2d")?.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  for (const quality of [0.9, 0.8, 0.65]) {
    const blob = await canvasToJpeg(canvas, quality);
    if (blob && blob.size <= MAX_UPLOAD_BYTES) {
      return new File([blob], file.name.replace(/\.[^.]+$/, "") + ".jpg", { type: "image/jpeg" });
    }
  }
  throw new Error("This photo is too large to upload, even after shrinking.");
}
