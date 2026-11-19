import { useLoader } from "@/hooks/useLoader";
import type { Outfit, OutfitList } from "@/types/outfit";
import { getOutfit, listOutfits } from "../api";

export function useOutfits(version: number) {
  return useLoader<OutfitList>(`${version}`, () => listOutfits());
}

export function useOutfit(id: string, version: number) {
  return useLoader<Outfit>(`${version}|${id}`, () => getOutfit(id));
}
