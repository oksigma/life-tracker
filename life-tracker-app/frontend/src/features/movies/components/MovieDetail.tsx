"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Modal } from "@/components/ui/Modal";
import { useLoader } from "@/hooks/useLoader";
import { ApiError, errorMessage } from "@/lib/api";
import { formatDate } from "@/lib/dates";
import { formatRuntime, tmdbMovieUrl } from "@/lib/tmdb";
import type { Movie } from "@/types/movie";
import { attachDetails, deleteMovie, removeDetails, tmdbConfigured, updateMovie } from "../api";
import { useMovie } from "../hooks/useMovies";
import { formatWatchedOn, WHERE_LABELS } from "../utils";
import { ChangeMatch } from "./ChangeMatch";
import { MovieForm } from "./MovieForm";
import { Poster } from "./Poster";
import { StarDisplay } from "./StarRating";
import { TmdbAttribution } from "./TmdbResults";

type Dialog = "edit" | "delete" | "match" | null;

export function MovieDetail({ id }: { id: string }) {
  const router = useRouter();
  const [version, setVersion] = useState(0);
  const { data: movie, error, loading } = useMovie(id, version);
  const tmdb = useLoader("tmdb-status", tmdbConfigured);
  const [dialog, setDialog] = useState<Dialog>(null);
  const [detailsMessage, setDetailsMessage] = useState<string | null>(null);
  const [findingDetails, setFindingDetails] = useState(false);
  const close = () => setDialog(null);
  const reload = () => setVersion((v) => v + 1);

  async function findDetails(target: Movie) {
    setFindingDetails(true);
    setDetailsMessage(null);
    try {
      await attachDetails(target.id);
      reload();
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        setDetailsMessage("No automatic match found — search for it instead.");
        setDialog("match");
      } else {
        setDetailsMessage(errorMessage(e));
      }
    } finally {
      setFindingDetails(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-6 sm:py-8">
      <Link href="/movies" className="text-sm text-slate-500 hover:underline">
        ← All movies
      </Link>

      {error ? (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <p>{error === "Movie not found" ? "This movie entry doesn't exist." : `Couldn't load movie: ${error}`}</p>
          {error !== "Movie not found" && (
            <button type="button" className="mt-2 underline" onClick={reload}>
              Try again
            </button>
          )}
        </div>
      ) : !movie || (loading && movie.id !== id) ? (
        <div className="mt-4 space-y-3" aria-label="Loading">
          <div className="h-7 w-1/2 animate-pulse rounded bg-slate-200" />
          <div className="h-4 w-1/3 animate-pulse rounded bg-slate-100" />
        </div>
      ) : (
        <article className="mt-4 rounded-lg border border-slate-200 bg-white p-4 sm:p-6">
          <div className="flex gap-4">
            <Poster
              path={movie.details?.poster_path}
              title={movie.title}
              size="w185"
              className="h-36 w-24 shrink-0 text-3xl sm:h-48 sm:w-32"
            />
            <div className="min-w-0 flex-1">
              <h1 className="text-xl font-semibold sm:text-2xl">
                {movie.title}
                {movie.year && <span className="ml-2 font-normal text-slate-500">({movie.year})</span>}
              </h1>
              {movie.details && (
                <p className="mt-1 text-sm text-slate-600">
                  {[movie.details.runtime && formatRuntime(movie.details.runtime), movie.details.year]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
              )}
              {movie.details && movie.details.genres.length > 0 && (
                <ul className="mt-2 flex flex-wrap gap-1" aria-label="Genres">
                  {movie.details.genres.map((genre) => (
                    <li key={genre} className="rounded-full bg-violet-50 px-2 py-0.5 text-xs text-violet-700 ring-1 ring-violet-200">
                      {genre}
                    </li>
                  ))}
                </ul>
              )}
              <div className="mt-3">
                <StarDisplay rating={movie.rating} />
              </div>
            </div>
          </div>

          <div className="mt-4 flex gap-2">
            <button type="button" className="btn-secondary flex-1 sm:flex-none" onClick={() => setDialog("edit")}>
              Edit
            </button>
            <button type="button" className="btn-danger flex-1 sm:flex-none" onClick={() => setDialog("delete")}>
              Delete
            </button>
          </div>

          <dl className="mt-6 grid grid-cols-[auto_1fr] gap-x-6 gap-y-3 text-sm">
            <dt className="text-slate-500">Watched</dt>
            <dd>{formatWatchedOn(movie.watched_on)}</dd>
            <dt className="text-slate-500">Where</dt>
            <dd>{movie.where ? WHERE_LABELS[movie.where] : <span className="text-slate-400">—</span>}</dd>
            {movie.notes && (
              <>
                <dt className="text-slate-500">Comments</dt>
                <dd className="whitespace-pre-wrap">{movie.notes}</dd>
              </>
            )}
          </dl>

          {movie.details?.overview && (
            <Collapsible title="Plot summary">
              <p className="leading-relaxed text-slate-700">{movie.details.overview}</p>
            </Collapsible>
          )}

          {movie.details && (
            <Collapsible title="More info">
              <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2">
                {movie.details.original_title && movie.details.original_title !== movie.details.title && (
                  <>
                    <dt className="text-slate-500">Original title</dt>
                    <dd>{movie.details.original_title}</dd>
                  </>
                )}
                {movie.details.release_date && (
                  <>
                    <dt className="text-slate-500">Released</dt>
                    <dd>{formatDate(movie.details.release_date)}</dd>
                  </>
                )}
                {movie.details.runtime && (
                  <>
                    <dt className="text-slate-500">Runtime</dt>
                    <dd>{formatRuntime(movie.details.runtime)}</dd>
                  </>
                )}
                <dt className="text-slate-500">TMDB</dt>
                <dd>
                  <a href={tmdbMovieUrl(movie.details.tmdb_id)} target="_blank" rel="noreferrer" className="underline">
                    View on TMDB
                  </a>
                </dd>
              </dl>
            </Collapsible>
          )}

          {tmdb.data && (
            <div className="mt-4 border-t border-slate-100 pt-4 text-sm">
              {movie.details ? (
                <div className="flex flex-wrap gap-x-4 gap-y-1">
                  <button type="button" className="text-slate-600 underline" onClick={() => setDialog("match")}>
                    Wrong movie?
                  </button>
                  <button
                    type="button"
                    className="text-slate-600 underline"
                    onClick={async () => {
                      try {
                        await removeDetails(movie.id);
                        reload();
                      } catch (e) {
                        setDetailsMessage(errorMessage(e));
                      }
                    }}
                  >
                    Remove details
                  </button>
                </div>
              ) : (
                <button type="button" className="btn-secondary" disabled={findingDetails} onClick={() => findDetails(movie)}>
                  {findingDetails ? "Finding details…" : "Find poster & details"}
                </button>
              )}
              {detailsMessage && <p className="mt-2 text-slate-600">{detailsMessage}</p>}
            </div>
          )}

          {dialog === "edit" && (
            <Modal title="Edit movie" onClose={close}>
              <MovieForm
                initial={movie}
                submitLabel="Save changes"
                onCancel={close}
                onSubmit={async (input) => {
                  await updateMovie(movie.id, input);
                  close();
                  reload();
                }}
              />
            </Modal>
          )}

          {dialog === "match" && (
            <Modal title="Find the right movie" onClose={close}>
              <ChangeMatch
                movie={movie}
                onCancel={close}
                onPicked={async (tmdbId) => {
                  await attachDetails(movie.id, tmdbId);
                  close();
                  setDetailsMessage(null);
                  reload();
                }}
              />
            </Modal>
          )}

          {dialog === "delete" && (
            <ConfirmDialog
              title="Delete movie?"
              message={`“${movie.title}” watched on ${formatWatchedOn(movie.watched_on)} will be permanently deleted.`}
              confirmLabel="Delete"
              onClose={close}
              onConfirm={async () => {
                await deleteMovie(movie.id);
                router.push("/movies");
              }}
            />
          )}
        </article>
      )}

      {movie?.details && <TmdbAttribution />}
    </main>
  );
}

/** A section that's closed by default, so long text doesn't take up space. */
function Collapsible({ title, children }: { title: string; children: ReactNode }) {
  return (
    <details className="group mt-4 rounded-lg border border-slate-200 text-sm">
      <summary className="flex cursor-pointer list-none items-center justify-between px-4 py-3 font-medium [&::-webkit-details-marker]:hidden">
        {title}
        <span className="text-slate-400 transition group-open:rotate-180" aria-hidden>
          ▾
        </span>
      </summary>
      <div className="border-t border-slate-100 px-4 py-3">{children}</div>
    </details>
  );
}
