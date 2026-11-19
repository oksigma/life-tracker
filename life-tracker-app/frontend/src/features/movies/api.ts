import { api } from "@/lib/api";
import type { Movie, MovieInput, MovieList, TmdbMatch } from "@/types/movie";

export function listMovies(query: string, limit = 200): Promise<MovieList> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (query) params.set("q", query);
  return api<MovieList>(`/api/movies?${params}`);
}

export function getMovie(id: string): Promise<Movie> {
  return api<Movie>(`/api/movies/${encodeURIComponent(id)}`);
}

export function createMovie(input: MovieInput): Promise<Movie> {
  return api<Movie>("/api/movies", { method: "POST", body: JSON.stringify(input) });
}

export function updateMovie(id: string, input: Partial<MovieInput>): Promise<Movie> {
  return api<Movie>(`/api/movies/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function deleteMovie(id: string): Promise<void> {
  return api<void>(`/api/movies/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export async function tmdbConfigured(): Promise<boolean> {
  return (await api<{ configured: boolean }>("/api/movies/tmdb/status")).configured;
}

export async function searchTmdb(query: string, year?: number | null): Promise<TmdbMatch[]> {
  const params = new URLSearchParams({ q: query });
  if (year) params.set("year", String(year));
  return (await api<{ results: TmdbMatch[] }>(`/api/movies/tmdb/search?${params}`)).results;
}

/** Match a movie to TMDB: a specific TMDB movie, or the best match for its title. */
export function attachDetails(id: string, tmdbId?: number): Promise<Movie> {
  return api<Movie>(`/api/movies/${encodeURIComponent(id)}/details`, {
    method: "POST",
    body: JSON.stringify(tmdbId ? { tmdb_id: tmdbId } : {}),
  });
}

export function removeDetails(id: string): Promise<Movie> {
  return api<Movie>(`/api/movies/${encodeURIComponent(id)}/details`, { method: "DELETE" });
}
