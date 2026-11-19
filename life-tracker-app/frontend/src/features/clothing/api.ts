import { api } from "@/lib/api";
import { prepareForUpload } from "@/lib/photos";
import type { Outfit, OutfitList, OutfitUpdate } from "@/types/outfit";

const BASE = "/api/clothing/outfits";

export function listOutfits(limit = 200): Promise<OutfitList> {
  return api<OutfitList>(`${BASE}?limit=${limit}`);
}

export function getOutfit(id: string): Promise<Outfit> {
  return api<Outfit>(`${BASE}/${encodeURIComponent(id)}`);
}

export async function uploadOutfit(photo: File, wornOn: string, notes: string | null): Promise<Outfit> {
  const form = new FormData();
  form.append("photo", await prepareForUpload(photo));
  form.append("worn_on", wornOn);
  if (notes) form.append("notes", notes);
  return api<Outfit>(BASE, { method: "POST", body: form });
}

export function updateOutfit(id: string, changes: OutfitUpdate): Promise<Outfit> {
  return api<Outfit>(`${BASE}/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify(changes),
  });
}

export function deleteOutfit(id: string): Promise<void> {
  return api<void>(`${BASE}/${encodeURIComponent(id)}`, { method: "DELETE" });
}
