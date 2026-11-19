// Mirrors backend/app/modules/calendar/schemas.py
import type { Meal } from "./food";
import type { Movie } from "./movie";
import type { Outfit } from "./outfit";

export type CalendarAreaKey = "movies" | "clothing" | "food";

export type CalendarDay = {
  date: string;
  counts: Partial<Record<CalendarAreaKey, number>>;
};

export type CalendarRange = {
  start: string;
  end: string;
  days: CalendarDay[];
};

export type DayEntries = {
  date: string;
  movies: Movie[];
  clothing: Outfit[];
  food: Meal[];
};
