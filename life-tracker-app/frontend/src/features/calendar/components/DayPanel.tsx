"use client";

import Link from "next/link";
import { ApiImage } from "@/components/ui/ApiImage";
import { formatDayHeading } from "@/lib/dates";
import { formatKcal, MEAL_LABELS, summariseItems } from "@/features/food/utils";
import { StarDisplay } from "@/features/movies/components/StarRating";
import { CALENDAR_AREAS } from "../areas";
import { useDayEntries } from "../hooks/useCalendar";

const AREA = Object.fromEntries(CALENDAR_AREAS.map((a) => [a.key, a]));

type DayPanelProps = {
  day: string;
  /** From the month data: skip the request for days with nothing logged. */
  hasEntries: boolean;
  version: number;
};

export function DayPanel({ day, hasEntries, version }: DayPanelProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <h2 className="font-semibold">{formatDayHeading(day)}</h2>
      {hasEntries ? (
        <DayEntriesList day={day} version={version} />
      ) : (
        <p className="mt-2 text-sm text-slate-500">Nothing logged on this day.</p>
      )}
    </div>
  );
}

function DayEntriesList({ day, version }: { day: string; version: number }) {
  const { data, error } = useDayEntries(day, version);

  if (error) return <p className="mt-2 text-sm text-red-600">Couldn&apos;t load this day: {error}</p>;
  if (!data || data.date !== day) {
    return <div className="mt-3 h-20 animate-pulse rounded bg-slate-100" aria-label="Loading" />;
  }

  return (
    <div className="mt-3 space-y-4">
      {data.movies.length > 0 && (
        <section>
          <h3 className="mb-2 text-sm font-medium text-slate-600">
            <span aria-hidden>{AREA.movies.symbol}</span> Movies
          </h3>
          <ul className="space-y-1">
            {data.movies.map((movie) => (
              <li key={movie.id}>
                <Link href={`/movies/${movie.id}`} className="flex items-center justify-between gap-2 rounded px-2 py-1 hover:bg-slate-50">
                  <span className="truncate">
                    {movie.title}
                    {movie.year && <span className="ml-1 text-slate-500">({movie.year})</span>}
                  </span>
                  <StarDisplay rating={movie.rating} />
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {data.food.length > 0 && (
        <section>
          <h3 className="mb-2 flex justify-between text-sm font-medium text-slate-600">
            <span>
              <span aria-hidden>{AREA.food.symbol}</span> Food
            </span>
            <span>{formatKcal(data.food.reduce((sum, meal) => sum + meal.total_kcal, 0))}</span>
          </h3>
          <ul className="space-y-1">
            {data.food.map((meal) => (
              <li key={meal.id}>
                <Link href={`/food/${meal.id}`} className="flex items-center justify-between gap-2 rounded px-2 py-1 hover:bg-slate-50">
                  <span className="min-w-0">
                    <span className="block">{MEAL_LABELS[meal.meal_type]}</span>
                    <span className="block truncate text-xs text-slate-500">{summariseItems(meal.items)}</span>
                  </span>
                  <span className="shrink-0 text-sm">{formatKcal(meal.total_kcal)}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {data.clothing.length > 0 && (
        <section>
          <h3 className="mb-2 text-sm font-medium text-slate-600">
            <span aria-hidden>{AREA.clothing.symbol}</span> Clothing
          </h3>
          <ul className="grid grid-cols-3 gap-2">
            {data.clothing.map((outfit) => (
              <li key={outfit.id}>
                <Link href={`/clothing/${outfit.id}`} className="block overflow-hidden rounded-md border border-slate-200 hover:opacity-90">
                  <ApiImage path={outfit.thumbnail_url} alt={outfit.notes ?? "Outfit"} className="aspect-[3/4] w-full object-cover" />
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
