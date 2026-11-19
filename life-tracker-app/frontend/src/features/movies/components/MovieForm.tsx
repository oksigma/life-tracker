"use client";

import { useState, type FormEvent } from "react";
import { useLoader } from "@/hooks/useLoader";
import { errorMessage } from "@/lib/api";
import { WHERE_WATCHED, type Movie, type MovieInput, type TmdbMatch, type WhereWatched } from "@/types/movie";
import { tmdbConfigured } from "../api";
import { FIRST_FILM_YEAR, todayLocal, WHERE_LABELS } from "../utils";
import { StarInput } from "./StarRating";
import { TitleSuggestions } from "./TitleSuggestions";

type MovieFormProps = {
  initial?: Movie;
  submitLabel: string;
  onSubmit: (input: MovieInput) => Promise<void>;
  onCancel: () => void;
};

type Errors = Partial<Record<"title" | "watched_on" | "year" | "notes", string>>;

function validate(values: { title: string; watchedOn: string; year: string; notes: string }): Errors {
  const errors: Errors = {};
  const maxYear = new Date().getFullYear() + 1;
  if (!values.title.trim()) errors.title = "Enter a title.";
  else if (values.title.trim().length > 200) errors.title = "Title must be 200 characters or fewer.";
  if (!values.watchedOn) errors.watched_on = "Enter the date you watched it.";
  else if (values.watchedOn > todayLocal()) errors.watched_on = "The date can't be in the future.";
  if (values.year) {
    const year = Number(values.year);
    if (!Number.isInteger(year) || year < FIRST_FILM_YEAR || year > maxYear) {
      errors.year = `Year must be between ${FIRST_FILM_YEAR} and ${maxYear}.`;
    }
  }
  if (values.notes.length > 2000) errors.notes = "Comments must be 2000 characters or fewer.";
  return errors;
}

export function MovieForm({ initial, submitLabel, onSubmit, onCancel }: MovieFormProps) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [watchedOn, setWatchedOn] = useState(initial?.watched_on ?? todayLocal());
  const [year, setYear] = useState(initial?.year?.toString() ?? "");
  const [rating, setRating] = useState<number | null>(initial?.rating ?? null);
  const [where, setWhere] = useState<WhereWatched | "">(initial?.where ?? "");
  const [notes, setNotes] = useState(initial?.notes ?? "");
  const [errors, setErrors] = useState<Errors>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [picked, setPicked] = useState<TmdbMatch | null>(null);
  const isNew = !initial;
  // Suggestions only for new movies; existing ones change their match from the movie page.
  const tmdb = useLoader(isNew ? "tmdb-status" : "", () => (isNew ? tmdbConfigured() : Promise.resolve(false)));

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const found = validate({ title, watchedOn, year, notes });
    setErrors(found);
    if (Object.keys(found).length > 0) return;

    setSaving(true);
    setServerError(null);
    try {
      await onSubmit({
        title: title.trim(),
        watched_on: watchedOn,
        year: year ? Number(year) : null,
        rating,
        where: where || null,
        notes: notes.trim() || null,
        ...(isNew ? { tmdb_id: picked?.tmdb_id ?? null } : {}),
      });
    } catch (e) {
      setServerError(errorMessage(e));
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <Field label="Title" htmlFor="movie-title" error={errors.title}>
        <input
          id="movie-title"
          className="input"
          value={title}
          onChange={(e) => {
            setTitle(e.target.value);
            setPicked(null);
          }}
          maxLength={200}
          autoFocus
          autoComplete="off"
          aria-invalid={!!errors.title}
        />
        {isNew && tmdb.data === true && (
          <TitleSuggestions
            title={title}
            picked={picked}
            onPick={(match) => {
              setPicked(match);
              setTitle(match.title);
              if (match.year) setYear(String(match.year));
            }}
            onClear={() => setPicked(null)}
          />
        )}
        {isNew && tmdb.data === false && (
          <p className="mt-1 text-xs text-slate-500">
            Tip: add a free TMDB key to the app&apos;s <code>.env</code> file to get posters and details automatically.
          </p>
        )}
      </Field>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Date watched" htmlFor="movie-watched-on" error={errors.watched_on}>
          <input
            id="movie-watched-on"
            type="date"
            className="input"
            value={watchedOn}
            max={todayLocal()}
            onChange={(e) => setWatchedOn(e.target.value)}
            aria-invalid={!!errors.watched_on}
          />
        </Field>
        <Field label="Release year" htmlFor="movie-year" error={errors.year} optional>
          <input
            id="movie-year"
            type="number"
            inputMode="numeric"
            className="input"
            value={year}
            min={FIRST_FILM_YEAR}
            onChange={(e) => setYear(e.target.value)}
            aria-invalid={!!errors.year}
          />
        </Field>
      </div>

      <Field label="Rating" optional>
        <StarInput value={rating} onChange={setRating} />
      </Field>

      <Field label="Where watched" htmlFor="movie-where" optional>
        <select
          id="movie-where"
          className="input"
          value={where}
          onChange={(e) => setWhere(e.target.value as WhereWatched | "")}
        >
          <option value="">—</option>
          {WHERE_WATCHED.map((option) => (
            <option key={option} value={option}>
              {WHERE_LABELS[option]}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Comments" htmlFor="movie-notes" error={errors.notes} optional>
        <textarea
          id="movie-notes"
          className="input min-h-24"
          value={notes}
          maxLength={2000}
          onChange={(e) => setNotes(e.target.value)}
          aria-invalid={!!errors.notes}
        />
      </Field>

      {serverError && <p className="text-sm text-red-600">{serverError}</p>}

      <div className="flex justify-end gap-2 pt-2">
        <button type="button" onClick={onCancel} className="btn-secondary">
          Cancel
        </button>
        <button type="submit" disabled={saving} className="btn-primary">
          {saving ? "Saving…" : submitLabel}
        </button>
      </div>
    </form>
  );
}

type FieldProps = {
  label: string;
  htmlFor?: string;
  error?: string;
  optional?: boolean;
  children: React.ReactNode;
};

function Field({ label, htmlFor, error, optional, children }: FieldProps) {
  return (
    <div>
      <label htmlFor={htmlFor} className="mb-1 block text-sm font-medium text-slate-700">
        {label}
        {optional && <span className="ml-1 font-normal text-slate-400">(optional)</span>}
      </label>
      {children}
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
}
