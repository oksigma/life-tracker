import type { CalendarAreaKey } from "@/types/calendar";

export type CalendarArea = {
  key: CalendarAreaKey;
  label: string;
  symbol: string;
  singular: string;
  plural: string;
  /** Tailwind classes for the day-cell chip. Icon + colour, so it never relies on colour alone. */
  chipClass: string;
};

/**
 * Life areas shown on the calendar, in display order.
 * To add one (e.g. health ❤️ rose, drinks 🥤 emerald), add it to the backend
 * CalendarService and DayEntries, to `CalendarAreaKey`, and here.
 */
export const CALENDAR_AREAS: CalendarArea[] = [
  {
    key: "movies",
    label: "Movies",
    symbol: "🎬",
    singular: "movie",
    plural: "movies",
    chipClass: "bg-violet-100 text-violet-800 ring-violet-300",
  },
  {
    key: "clothing",
    label: "Clothing",
    symbol: "👕",
    singular: "outfit",
    plural: "outfits",
    chipClass: "bg-sky-100 text-sky-800 ring-sky-300",
  },
  {
    key: "food",
    label: "Food",
    symbol: "🍽️",
    singular: "meal",
    plural: "meals",
    chipClass: "bg-amber-100 text-amber-800 ring-amber-300",
  },
];

export function describeCounts(counts: Partial<Record<CalendarAreaKey, number>>): string {
  return CALENDAR_AREAS.filter((area) => counts[area.key])
    .map((area) => {
      const n = counts[area.key]!;
      return `${n} ${n === 1 ? area.singular : area.plural}`;
    })
    .join(", ");
}
