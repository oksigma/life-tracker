import type { Metadata } from "next";
import { OutfitDetail } from "@/features/clothing/components/OutfitDetail";

export const metadata: Metadata = { title: "Outfit · LifeTracker" };

export default async function OutfitDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <OutfitDetail id={id} />;
}
