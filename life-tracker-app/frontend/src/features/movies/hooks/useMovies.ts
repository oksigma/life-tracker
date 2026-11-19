import { useLoader } from "@/hooks/useLoader";
import type { Movie, MovieList } from "@/types/movie";
import { getMovie, listMovies } from "../api";

export function useMovies(query: string, version: number) {
  return useLoader<MovieList>(`${version}|${query}`, () => listMovies(query));
}

export function useMovie(id: string, version: number) {
  return useLoader<Movie>(`${version}|${id}`, () => getMovie(id));
}
