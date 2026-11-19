export type PosterSize = "w92" | "w185" | "w342";

/** Poster image URL on TMDB's image server. */
export function posterUrl(path: string, size: PosterSize = "w185"): string {
  return `https://image.tmdb.org/t/p/${size}${path}`;
}

export function tmdbMovieUrl(tmdbId: number): string {
  return `https://www.themoviedb.org/movie/${tmdbId}`;
}

/** e.g. 155 → "2h 35m". */
export function formatRuntime(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h ? `${h}h${m ? ` ${m}m` : ""}` : `${m}m`;
}
