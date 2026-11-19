import { useLoader } from "@/hooks/useLoader";
import type { Meal, MealList } from "@/types/food";
import { getMeal, listMeals } from "../api";

export function useMeals(version: number) {
  return useLoader<MealList>(`${version}`, () => listMeals());
}

export function useMeal(id: string, version: number) {
  return useLoader<Meal>(`${version}|${id}`, () => getMeal(id));
}
