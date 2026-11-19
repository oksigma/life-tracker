"use client";

import Link from "next/link";
import { useState } from "react";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Modal } from "@/components/ui/Modal";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import type { Movie } from "@/types/movie";
import { createMovie, deleteMovie, updateMovie } from "../api";
import { useMovies } from "../hooks/useMovies";
import { formatWatchedOn, WHERE_LABELS } from "../utils";
import { formatRuntime } from "@/lib/tmdb";
import { MovieForm } from "./MovieForm";
import { Poster } from "./Poster";
import { StarDisplay } from "./StarRating";
import { TmdbAttribution } from "./TmdbResults";

type Dialog = { kind: "add" } | { kind: "edit"; movie: Movie } | { kind: "delete"; movie: Movie } | null;

export function MoviesView() {
  const [search, setSearch] = useState("");
  const query = useDebouncedValue(search.trim());
  const [version, setVersion] = useState(0);
  const { data, error, loading } = useMovies(query, version);
  const [dialog, setDialog] = useState<Dialog>(null);

  const reload = () => setVersion((v) => v + 1);
  const close = () => setDialog(null);

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <div className="flex items-center justify-between gap-4">
        <div>
          <Link href="/" className="text-sm text-slate-500 hover:underline">
            ← LifeTracker
          </Link>
          <h1 className="text-2xl font-semibold">Movies</h1>
        </div>
        <button type="button" className="btn-primary" onClick={() => setDialog({ kind: "add" })}>
          Log a movie
        </button>
      </div>

      <input
        type="search"
        placeholder="Search titles…"
        aria-label="Search titles"
        className="input mt-6"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <section className="mt-4" aria-busy={loading}>
        {error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <p>Couldn&apos;t load movies: {error}</p>
            <button type="button" className="mt-2 underline" onClick={reload}>
              Try again
            </button>
          </div>
        ) : !data ? (
          <ListSkeleton />
        ) : data.items.length === 0 ? (
          <EmptyState searching={!!query} onAdd={() => setDialog({ kind: "add" })} />
        ) : (
          <>
            <p className="mb-2 text-sm text-slate-500">
              {data.total} {data.total === 1 ? "movie" : "movies"}
              {query && ` matching “${query}”`}
            </p>
            <ul className={`divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white ${loading ? "opacity-60" : ""}`}>
              {data.items.map((movie) => (
                <li key={movie.id} className="flex items-center gap-3 px-3 py-2 sm:gap-4 sm:px-4 sm:py-3">
                  <Link href={`/movies/${movie.id}`} className="shrink-0" tabIndex={-1} aria-hidden>
                    <Poster path={movie.details?.poster_path} title={movie.title} size="w92" className="h-16 w-11 text-xl" />
                  </Link>
                  <Link href={`/movies/${movie.id}`} className="min-w-0 flex-1">
                    <p className="truncate font-medium hover:underline">
                      {movie.title}
                      {movie.year && <span className="ml-1 font-normal text-slate-500">({movie.year})</span>}
                    </p>
                    <p className="text-sm text-slate-500">
                      {formatWatchedOn(movie.watched_on)}
                      {movie.where && ` · ${WHERE_LABELS[movie.where]}`}
                    </p>
                    {movie.details && (movie.details.runtime || movie.details.genres.length > 0) && (
                      <p className="truncate text-xs text-slate-400">
                        {[movie.details.runtime && formatRuntime(movie.details.runtime), movie.details.genres.slice(0, 3).join(", ")]
                          .filter(Boolean)
                          .join(" · ")}
                      </p>
                    )}
                    {movie.notes && (
                      <p className="mt-0.5 line-clamp-2 text-sm text-slate-600 italic" title={movie.notes}>
                        “{movie.notes}”
                      </p>
                    )}
                  </Link>
                  <span className="shrink-0 text-sm">
                    <StarDisplay rating={movie.rating} />
                  </span>
                  {/* On phones, edit/delete live on the movie's page to keep rows uncluttered. */}
                  <div className="hidden gap-1 sm:flex">
                    <button
                      type="button"
                      className="rounded px-2 py-1 text-sm text-slate-600 hover:bg-slate-100"
                      onClick={() => setDialog({ kind: "edit", movie })}
                      aria-label={`Edit ${movie.title}`}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="rounded px-2 py-1 text-sm text-red-600 hover:bg-red-50"
                      onClick={() => setDialog({ kind: "delete", movie })}
                      aria-label={`Delete ${movie.title}`}
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      <TmdbAttribution />

      {dialog?.kind === "add" && (
        <Modal title="Log a movie" onClose={close}>
          <MovieForm
            submitLabel="Save"
            onCancel={close}
            onSubmit={async (input) => {
              await createMovie(input);
              close();
              reload();
            }}
          />
        </Modal>
      )}

      {dialog?.kind === "edit" && (
        <Modal title="Edit movie" onClose={close}>
          <MovieForm
            initial={dialog.movie}
            submitLabel="Save changes"
            onCancel={close}
            onSubmit={async (input) => {
              await updateMovie(dialog.movie.id, input);
              close();
              reload();
            }}
          />
        </Modal>
      )}

      {dialog?.kind === "delete" && (
        <ConfirmDialog
          title="Delete movie?"
          message={`“${dialog.movie.title}” watched on ${formatWatchedOn(dialog.movie.watched_on)} will be permanently deleted.`}
          confirmLabel="Delete"
          onClose={close}
          onConfirm={async () => {
            await deleteMovie(dialog.movie.id);
            close();
            reload();
          }}
        />
      )}
    </main>
  );
}

function EmptyState({ searching, onAdd }: { searching: boolean; onAdd: () => void }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-white p-10 text-center">
      {searching ? (
        <p className="text-slate-500">No movies match your search.</p>
      ) : (
        <>
          <p className="text-slate-500">No movies logged yet.</p>
          <button type="button" className="btn-primary mt-4" onClick={onAdd}>
            Log a movie
          </button>
        </>
      )}
    </div>
  );
}

function ListSkeleton() {
  return (
    <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white" aria-label="Loading">
      {[0, 1, 2].map((i) => (
        <li key={i} className="px-4 py-3">
          <div className="h-4 w-1/2 animate-pulse rounded bg-slate-200" />
          <div className="mt-2 h-3 w-1/4 animate-pulse rounded bg-slate-100" />
        </li>
      ))}
    </ul>
  );
}
