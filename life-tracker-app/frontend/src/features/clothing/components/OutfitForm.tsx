"use client";

import { useState, type FormEvent } from "react";
import { ApiImage } from "@/components/ui/ApiImage";
import { PhotoPicker } from "@/components/ui/PhotoPicker";
import { errorMessage } from "@/lib/api";
import { todayLocal } from "@/lib/dates";
import type { Outfit } from "@/types/outfit";
import { MAX_NOTES } from "../utils";

export type OutfitFormValues = { photo: File | null; wornOn: string; notes: string | null };

type OutfitFormProps = {
  /** When given, the form edits this outfit's date and notes; the photo can't be changed. */
  initial?: Outfit;
  submitLabel: string;
  onSubmit: (values: OutfitFormValues) => Promise<void>;
  onCancel: () => void;
};

export function OutfitForm({ initial, submitLabel, onSubmit, onCancel }: OutfitFormProps) {
  const isNew = !initial;
  const [photo, setPhoto] = useState<File | null>(null);
  const [wornOn, setWornOn] = useState(initial?.worn_on ?? todayLocal());
  const [notes, setNotes] = useState(initial?.notes ?? "");
  const [errors, setErrors] = useState<{ photo?: string; wornOn?: string; notes?: string }>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const found: typeof errors = {};
    if (isNew && !photo) found.photo = "Choose a photo of your outfit.";
    if (!wornOn) found.wornOn = "Enter the date you wore it.";
    else if (wornOn > todayLocal()) found.wornOn = "The date can't be in the future.";
    if (notes.length > MAX_NOTES) found.notes = `Notes must be ${MAX_NOTES} characters or fewer.`;
    setErrors(found);
    if (Object.keys(found).length > 0) return;

    setSaving(true);
    setServerError(null);
    try {
      await onSubmit({ photo, wornOn, notes: notes.trim() || null });
    } catch (e) {
      setServerError(errorMessage(e));
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      {isNew ? (
        <PhotoPicker photo={photo} onChange={setPhoto} error={errors.photo} />
      ) : (
        <ApiImage path={initial.thumbnail_url} alt="Outfit" className="h-40 w-32 rounded-lg object-cover" />
      )}

      <div>
        <label htmlFor="outfit-worn-on" className="mb-1 block text-sm font-medium text-slate-700">
          Date worn
        </label>
        <input
          id="outfit-worn-on"
          type="date"
          className="input"
          value={wornOn}
          max={todayLocal()}
          onChange={(e) => setWornOn(e.target.value)}
          aria-invalid={!!errors.wornOn}
        />
        {isNew && !errors.wornOn && (
          <p className="mt-1 text-xs text-slate-500">Defaults to today — change it if you&apos;re logging an earlier day.</p>
        )}
        {errors.wornOn && <p className="mt-1 text-sm text-red-600">{errors.wornOn}</p>}
      </div>

      <div>
        <label htmlFor="outfit-notes" className="mb-1 block text-sm font-medium text-slate-700">
          Notes <span className="font-normal text-slate-400">(optional)</span>
        </label>
        <textarea
          id="outfit-notes"
          className="input min-h-20"
          value={notes}
          maxLength={MAX_NOTES}
          placeholder="e.g. Work, dinner out, the new jacket"
          onChange={(e) => setNotes(e.target.value)}
          aria-invalid={!!errors.notes}
        />
        {errors.notes && <p className="mt-1 text-sm text-red-600">{errors.notes}</p>}
      </div>

      {serverError && <p className="text-sm text-red-600">{serverError}</p>}

      <div className="flex justify-end gap-2 pt-2">
        <button type="button" onClick={onCancel} className="btn-secondary">
          Cancel
        </button>
        <button type="submit" disabled={saving} className="btn-primary">
          {saving ? (isNew ? "Uploading…" : "Saving…") : submitLabel}
        </button>
      </div>
    </form>
  );
}
