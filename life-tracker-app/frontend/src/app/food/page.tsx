import type { Metadata } from "next";
import { FoodView } from "@/features/food/components/FoodView";

export const metadata: Metadata = { title: "Food · LifeTracker" };

export default function FoodPage() {
  return <FoodView />;
}
