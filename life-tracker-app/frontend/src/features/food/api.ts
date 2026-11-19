import { api } from "@/lib/api";
import type { FoodLookup, Meal, MealItemInput, MealList, MealType, MealUpdate, SavedFood } from "@/types/food";

const BASE = "/api/food";

export function listMeals(limit = 200): Promise<MealList> {
  return api<MealList>(`${BASE}/meals?limit=${limit}`);
}

export function getMeal(id: string): Promise<Meal> {
  return api<Meal>(`${BASE}/meals/${encodeURIComponent(id)}`);
}

export function createMeal(input: {
  photo: File | null;
  eatenOn: string;
  mealType: MealType;
  notes: string | null;
  items: MealItemInput[];
}): Promise<Meal> {
  const form = new FormData();
  if (input.photo) form.append("photo", input.photo);
  form.append("eaten_on", input.eatenOn);
  form.append("meal_type", input.mealType);
  if (input.notes) form.append("notes", input.notes);
  form.append("items", JSON.stringify(input.items));
  return api<Meal>(`${BASE}/meals`, { method: "POST", body: form });
}

export function updateMeal(id: string, changes: MealUpdate): Promise<Meal> {
  return api<Meal>(`${BASE}/meals/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(changes) });
}

export function deleteMeal(id: string): Promise<void> {
  return api<void>(`${BASE}/meals/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export async function searchMyFoods(query: string): Promise<SavedFood[]> {
  const params = new URLSearchParams({ limit: "8" });
  if (query) params.set("q", query);
  return (await api<{ items: SavedFood[] }>(`${BASE}/foods?${params}`)).items;
}

export function lookupFood(query: string): Promise<FoodLookup> {
  return api<FoodLookup>(`${BASE}/lookup?q=${encodeURIComponent(query)}`);
}
