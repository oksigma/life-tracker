import type { Metadata } from "next";
import { MealDetail } from "@/features/food/components/MealDetail";

export const metadata: Metadata = { title: "Meal · LifeTracker" };

export default async function MealDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <MealDetail id={id} />;
}
