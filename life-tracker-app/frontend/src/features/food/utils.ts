import type { FoodOption, MealItem, MealItemInput, MealType, Unit } from "@/types/food";

export const MAX_NOTES = 1000;
export const MAX_ITEMS = 50;

export const MEAL_LABELS: Record<MealType, string> = {
  breakfast: "Breakfast",
  lunch: "Lunch",
  dinner: "Dinner",
  snack: "Snack",
};

export const UNIT_LABELS: Record<Unit, string> = { g: "g", ml: "ml", serving: "serving(s)" };

/** A sensible meal type for the current time of day. */
export function defaultMealType(now = new Date()): MealType {
  const hour = now.getHours();
  if (hour < 11) return "breakfast";
  if (hour < 15) return "lunch";
  if (hour >= 17 && hour < 22) return "dinner";
  return "snack";
}

/** Mirrors the backend's calculation (backend/app/modules/food/schemas.py). */
export function calculateKcal(
  quantity: number | null,
  unit: Unit | null,
  kcalPer100g: number | null,
  kcalPerServing: number | null,
): number | null {
  if (quantity === null || unit === null) return null;
  if ((unit === "g" || unit === "ml") && kcalPer100g !== null) return (kcalPer100g * quantity) / 100;
  if (unit === "serving" && kcalPerServing !== null) return kcalPerServing * quantity;
  return null;
}

export function formatKcal(kcal: number): string {
  return `≈ ${Math.round(kcal).toLocaleString()} kcal`;
}

/** Units that can be used to calculate calories for a food. */
export function unitsFor(food: { kcal_per_100g: number | null; kcal_per_serving: number | null }): Unit[] {
  const units: Unit[] = [];
  if (food.kcal_per_100g !== null) units.push("g", "ml");
  if (food.kcal_per_serving !== null) units.push("serving");
  return units;
}

/** An item being edited in the meal form. Inputs are kept as strings while typing. */
export type DraftItem = {
  key: string;
  name: string;
  brand: string | null;
  source: FoodOption["source"];
  off_code: string | null;
  kcal_per_100g: number | null;
  kcal_per_serving: number | null;
  serving_size: string | null;
  quantity: string;
  unit: Unit | "";
  /** Typed calories, used when they can't be calculated (manual items). */
  kcal: string;
};

function newKey(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : String(Math.random());
}

export function draftFromOption(food: FoodOption): DraftItem {
  const useGrams = food.kcal_per_100g !== null;
  return {
    key: newKey(),
    name: food.name,
    brand: food.brand,
    source: food.source,
    off_code: food.off_code,
    kcal_per_100g: food.kcal_per_100g,
    kcal_per_serving: food.kcal_per_serving,
    serving_size: food.serving_size,
    quantity: useGrams ? "100" : "1",
    unit: useGrams ? "g" : "serving",
    kcal: "",
  };
}

export function manualDraft(name: string): DraftItem {
  return {
    key: newKey(),
    name,
    brand: null,
    source: "manual",
    off_code: null,
    kcal_per_100g: null,
    kcal_per_serving: null,
    serving_size: null,
    quantity: "",
    unit: "",
    kcal: "",
  };
}

export function draftFromItem(item: MealItem): DraftItem {
  return {
    key: newKey(),
    name: item.name,
    brand: item.brand,
    source: item.source,
    off_code: item.off_code,
    kcal_per_100g: item.kcal_per_100g,
    kcal_per_serving: item.kcal_per_serving,
    serving_size: null,
    quantity: item.quantity?.toString() ?? "",
    unit: item.unit ?? "",
    kcal: item.source === "manual" ? item.kcal.toString() : "",
  };
}

function parseNumber(value: string): number | null {
  if (value.trim() === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : NaN;
}

/** Calories for a draft item: calculated if possible, otherwise the typed value. */
export function draftKcal(item: DraftItem): number | null {
  const quantity = parseNumber(item.quantity);
  const unit = item.unit || null;
  if (quantity !== null && !Number.isNaN(quantity) && quantity > 0) {
    const computed = calculateKcal(quantity, unit, item.kcal_per_100g, item.kcal_per_serving);
    if (computed !== null) return computed;
  }
  const typed = parseNumber(item.kcal);
  return typed === null || Number.isNaN(typed) ? null : typed;
}

export function canCalculate(item: DraftItem): boolean {
  return item.unit !== "" && calculateKcal(1, item.unit, item.kcal_per_100g, item.kcal_per_serving) !== null;
}

/** Validation message for a draft item, or null if it's fine. */
export function draftError(item: DraftItem): string | null {
  if (!item.name.trim()) return "Enter a name.";
  const quantity = parseNumber(item.quantity);
  if (quantity !== null && (Number.isNaN(quantity) || quantity <= 0)) return "Amount must be more than 0.";
  if ((quantity === null) !== (item.unit === "")) return "Enter both an amount and a unit, or neither.";
  const kcal = draftKcal(item);
  if (kcal === null) return "Enter the calories.";
  if (kcal < 0 || kcal > 10_000) return "Calories must be between 0 and 10,000.";
  return null;
}

export function toItemInput(item: DraftItem): MealItemInput {
  const quantity = parseNumber(item.quantity);
  return {
    name: item.name.trim(),
    brand: item.brand,
    quantity: quantity === null || Number.isNaN(quantity) ? null : quantity,
    unit: item.unit || null,
    kcal_per_100g: item.kcal_per_100g,
    kcal_per_serving: item.kcal_per_serving,
    kcal: draftKcal(item),
    source: item.source,
    off_code: item.off_code,
  };
}

export function describeAmount(item: MealItem): string | null {
  if (item.quantity === null || item.unit === null) return null;
  const quantity = Number.isInteger(item.quantity) ? item.quantity : Number(item.quantity.toFixed(1));
  if (item.unit === "serving") return `${quantity} serving${quantity === 1 ? "" : "s"}`;
  return `${quantity} ${item.unit}`;
}

export function summariseItems(items: MealItem[]): string {
  if (items.length === 0) return "No foods added";
  const names = items.slice(0, 2).map((i) => i.name);
  return items.length > 2 ? `${names.join(", ")} +${items.length - 2} more` : names.join(", ");
}
