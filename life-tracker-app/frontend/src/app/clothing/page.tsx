import type { Metadata } from "next";
import { OutfitsView } from "@/features/clothing/components/OutfitsView";

export const metadata: Metadata = { title: "Clothing · LifeTracker" };

export default function ClothingPage() {
  return <OutfitsView />;
}
