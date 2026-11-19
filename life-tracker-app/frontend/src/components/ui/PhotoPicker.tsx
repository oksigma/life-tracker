"use client";

import { useEffect, useId, useRef, useState, type ChangeEvent } from "react";
import { ACCEPTED_PHOTO_TYPES, photoError } from "@/lib/photos";

type PhotoPickerProps = {
  photo: File | null;
  onChange: (photo: File | null) => void;
  /** Validation error from the parent form (e.g. "required"). */
  error?: string;
  optional?: boolean;
};

/** Take or choose a photo, with a preview. On phones the browser offers the camera. */
export function PhotoPicker({ photo, onChange, error, optional }: PhotoPickerProps) {
  const id = useId();
  const input = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewFailed, setPreviewFailed] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);

  // Release the local preview when it's replaced or the picker unmounts.
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  function choose(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = ""; // allow re-choosing the same file
    if (!file) return;
    const problem = photoError(file);
    setFileError(problem);
    setPreviewFailed(false);
    if (problem) {
      setPreviewUrl(null);
      onChange(null);
      return;
    }
    setPreviewUrl(URL.createObjectURL(file));
    onChange(file);
  }

  function remove() {
    setPreviewUrl(null);
    setFileError(null);
    onChange(null);
  }

  const shownError = fileError ?? error;

  return (
    <div>
      <span className="mb-1 block text-sm font-medium text-slate-700">
        Photo{optional && <span className="ml-1 font-normal text-slate-400">(optional)</span>}
      </span>
      <input ref={input} id={id} type="file" accept={ACCEPTED_PHOTO_TYPES} onChange={choose} className="sr-only" />
      {photo ? (
        <div className="flex items-start gap-4">
          <div className="flex h-40 w-32 items-center justify-center overflow-hidden rounded-lg bg-slate-100">
            {previewUrl && !previewFailed ? (
              // eslint-disable-next-line @next/next/no-img-element -- local blob preview
              <img
                src={previewUrl}
                alt="Preview of the chosen photo"
                className="h-full w-full object-cover"
                onError={() => setPreviewFailed(true)}
              />
            ) : (
              <span className="px-2 text-center text-xs text-slate-500">
                No preview for this format — it will be converted on upload
              </span>
            )}
          </div>
          <div className="min-w-0 text-sm">
            <p className="truncate font-medium">{photo.name}</p>
            <p className="text-slate-500">{(photo.size / (1024 * 1024)).toFixed(1)} MB</p>
            <button type="button" className="mt-2 block underline" onClick={() => input.current?.click()}>
              Choose a different photo
            </button>
            {optional && (
              <button type="button" className="mt-1 block text-red-600 underline" onClick={remove}>
                Remove photo
              </button>
            )}
          </div>
        </div>
      ) : (
        <label
          htmlFor={id}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 text-sm text-slate-600 hover:border-slate-400 ${optional ? "h-28" : "h-40"}`}
        >
          <span className="text-3xl" aria-hidden>
            📷
          </span>
          <span className="mt-2 font-medium">Take or choose a photo</span>
          <span className="text-xs text-slate-500">JPEG, PNG, WebP or HEIC, up to 15 MB</span>
        </label>
      )}
      {shownError && <p className="mt-1 text-sm text-red-600">{shownError}</p>}
    </div>
  );
}
