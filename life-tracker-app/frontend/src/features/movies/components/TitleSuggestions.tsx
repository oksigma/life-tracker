"use client";

import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { useLoader } from "@/hooks/useLoader";
import type { TmdbMatch } from "@/types/movie";
import { searchTmdb } from "../api";
import { Poster } from "./Poster";
import { TmdbResults } from "./TmdbResults";

type TitleSuggestionsProps = {
  title: string;
  picked: TmdbMatch | null;
  onPick: (match: TmdbMatch) => void;
  onClear: () => void;
};

/** TMDB suggestions under the title field while typing; shows the picked movie once chosen. */
export function TitleSuggestions({ title, picked, onPick, onClear }: TitleSuggestionsProps) {
  const query = useDebouncedValue(title.trim(), 300);
  const active = !picked && query.length >= 2;
  const { data, error, loading } = useLoader(`tmdb|${active ? query : ""}`, () =>
    active ? searchTmdb(query) : Promise.resolve([] as TmdbMatch[]),
  );

  if (picked) {
    return (
      <div className="mt-2 flex items-center gap-3 rounded-md border border-violet-200 bg-violet-50 p-2">
        <Poster path={picked.poster_path} title={picked.title} size="w92" className="h-14 w-10 shrink-0 text-lg" />
        <p className="min-w-0 flex-1 text-sm">
          <span className="block truncate font-medium">
            {picked.title}
            {picked.year && <span className="ml-1 font-normal text-slate-500">({picked.year})</span>}
          </span>
          <span className="text-xs text-violet-700">Details will be added from TMDB</span>
        </p>
        <button type="button" className="shrink-0 text-sm text-slate-600 underline" onClick={onClear}>
          Not this one
        </button>
      </div>
    );
  }
  if (!active) return null;
  if (error) return <p className="mt-1 text-xs text-slate-500">Couldn&apos;t load suggestions ({error}).</p>;
  if (!data || loading) return <p className="mt-1 text-xs text-slate-500">Looking up “{query}”…</p>;
  if (data.length === 0) {
    return <p className="mt-1 text-xs text-slate-500">No matches on TMDB — the movie will be saved without details.</p>;
  }
  return (
    <div className="mt-2">
      <p className="mb-1 text-xs text-slate-500">Pick the movie to add its poster and details:</p>
      <TmdbResults results={data} onPick={onPick} />
    </div>
  );
}
