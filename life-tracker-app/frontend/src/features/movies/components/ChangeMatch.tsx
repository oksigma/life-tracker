"use client";

import { useState, type FormEvent } from "react";
import { errorMessage } from "@/lib/api";
import type { Movie, TmdbMatch } from "@/types/movie";
import { searchTmdb } from "../api";
import { TmdbResults } from "./TmdbResults";

type ChangeMatchProps = {
  movie: Movie;
  onPicked: (tmdbId: number) => Promise<void>;
  onCancel: () => void;
};

export function ChangeMatch({ movie, onPicked, onCancel }: ChangeMatchProps) {
  const [query, setQuery] = useState(movie.title);
  const [results, setResults] = useState<TmdbMatch[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function search(event?: FormEvent) {
    event?.preventDefault();
    if (query.trim().length < 2) return;
    setBusy(true);
    setError(null);
    try {
      setResults(await searchTmdb(query.trim()));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  async function pick(match: TmdbMatch) {
    setBusy(true);
    setError(null);
    try {
      await onPicked(match.tmdb_id);
    } catch (e) {
      setError(errorMessage(e));
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      <form onSubmit={search} className="flex gap-2">
        <input
          className="input"
          aria-label="Search TMDB"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoFocus
        />
        <button type="submit" className="btn-primary shrink-0" disabled={busy}>
          Search
        </button>
      </form>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {results &&
        (results.length > 0 ? (
          <TmdbResults results={results} onPick={pick} selectedId={movie.details?.tmdb_id} />
        ) : (
          <p className="text-sm text-slate-500">No matches — try a different spelling or the original title.</p>
        ))}
      <div className="flex justify-end">
        <button type="button" className="btn-secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </div>
  );
}
