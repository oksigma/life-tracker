import type { Metadata } from "next";
import { MovieDetail } from "@/features/movies/components/MovieDetail";

export const metadata: Metadata = { title: "Movie · LifeTracker" };

export default async function MovieDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <MovieDetail id={id} />;
}
