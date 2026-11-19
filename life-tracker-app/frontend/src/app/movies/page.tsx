import type { Metadata } from "next";
import { MoviesView } from "@/features/movies/components/MoviesView";

export const metadata: Metadata = { title: "Movies · LifeTracker" };

export default function MoviesPage() {
  return <MoviesView />;
}
