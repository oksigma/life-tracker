// Mirrors backend/app/modules/food/schemas.py

export const MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"] as const;
export type MealType = (typeof MEAL_TYPES)[number];

export const UNITS = ["g", "ml", "serving"] as const;
export type Unit = (typeof UNITS)[number];

export type FoodSource = "openfoodfacts" | "manual";

export type MealItemInput = {
  name: string;
  brand: string | null;
  quantity: number | null;
  unit: Unit | null;
  kcal_per_100g: number | null;
  kcal_per_serving: number | null;
  /** Required for manual items; recalculated by the backend when it can be. */
  kcal: number | null;
  source: FoodSource;
  off_code: string | null;
};

export type MealItem = MealItemInput & { kcal: number };

export type Meal = {
  id: string;
  eaten_on: string;
  meal_type: MealType;
  notes: string | null;
  items: MealItem[];
  total_kcal: number;
  photo_url: string | null;
  thumbnail_url: string | null;
  created_at: string;
  updated_at: string;
};

export type MealList = { items: Meal[]; total: number };

export type MealUpdate = {
  eaten_on?: string;
  meal_type?: MealType;
  notes?: string | null;
  items?: MealItemInput[];
};

export type FoodOption = {
  name: string;
  brand: string | null;
  kcal_per_100g: number | null;
  kcal_per_serving: number | null;
  serving_size: string | null;
  source: FoodSource;
  off_code: string | null;
};

export type SavedFood = FoodOption & { id: string; use_count: number };

export type FoodLookup = { results: FoodOption[]; cached: boolean };
