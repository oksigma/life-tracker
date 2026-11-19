import type { TmdbMatch } from "@/types/movie";
import { Poster } from "./Poster";

type TmdbResultsProps = {
  results: TmdbMatch[];
  onPick: (match: TmdbMatch) => void;
  selectedId?: number | null;
};

export function TmdbResults({ results, onPick, selectedId }: TmdbResultsProps) {
  return (
    <ul className="max-h-72 divide-y divide-slate-100 overflow-y-auto rounded-md border border-slate-200 bg-white" role="listbox">
      {results.map((match) => (
        <li key={match.tmdb_id} role="option" aria-selected={match.tmdb_id === selectedId}>
          <button
            type="button"
            className={`flex w-full items-center gap-3 px-3 py-2 text-left hover:bg-slate-50 ${match.tmdb_id === selectedId ? "bg-slate-100" : ""}`}
            onClick={() => onPick(match)}
          >
            <Poster path={match.poster_path} title={match.title} size="w92" className="h-14 w-10 shrink-0 text-lg" />
            <span className="min-w-0">
              <span className="block truncate font-medium">
                {match.title}
                {match.year && <span className="ml-1 font-normal text-slate-500">({match.year})</span>}
              </span>
              {match.overview && <span className="line-clamp-2 text-xs text-slate-500">{match.overview}</span>}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}

export function TmdbAttribution() {
  return (
    <p className="mt-8 text-center text-xs text-slate-400">
      Movie details and posters from{" "}
      <a href="https://www.themoviedb.org" target="_blank" rel="noreferrer" className="underline">
        TMDB
      </a>
      . This product uses the TMDB API but is not endorsed or certified by TMDB.
    </p>
  );
}
