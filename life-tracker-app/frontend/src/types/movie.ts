// Mirrors backend/app/modules/movies/schemas.py

export const WHERE_WATCHED = ["cinema", "home", "streaming", "other"] as const;
export type WhereWatched = (typeof WHERE_WATCHED)[number];

/** A TMDB search result. */
export type TmdbMatch = {
  tmdb_id: number;
  title: string;
  original_title: string | null;
  year: number | null;
  poster_path: string | null;
  overview: string | null;
};

/** Details from TMDB stored with a movie. */
export type MovieDetails = TmdbMatch & {
  release_date: string | null;
  runtime: number | null;
  genres: string[];
};

export type Movie = {
  id: string;
  title: string;
  /** Calendar date, YYYY-MM-DD */
  watched_on: string;
  year: number | null;
  rating: number | null;
  where: WhereWatched | null;
  notes: string | null;
  details: MovieDetails | null;
  created_at: string;
  updated_at: string;
};

export type MovieInput = {
  title: string;
  watched_on: string;
  year: number | null;
  rating: number | null;
  where: WhereWatched | null;
  notes: string | null;
  /** New movies only: the TMDB movie picked from the suggestions. */
  tmdb_id?: number | null;
};

export type MovieList = {
  items: Movie[];
  total: number;
};
