"use client";

import Link from "next/link";
import { useState } from "react";
import { ApiImage } from "@/components/ui/ApiImage";
import { Modal } from "@/components/ui/Modal";
import { formatDayHeading } from "@/lib/dates";
import { groupByDay } from "@/lib/grouping";
import { createMeal } from "../api";
import { useMeals } from "../hooks/useMeals";
import { formatKcal, MEAL_LABELS, summariseItems } from "../utils";
import { MealForm } from "./MealForm";

export function FoodView() {
  const [version, setVersion] = useState(0);
  const { data, error, loading } = useMeals(version);
  const [adding, setAdding] = useState(false);
  const reload = () => setVersion((v) => v + 1);

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <div className="flex items-center justify-between gap-4">
        <div>
          <Link href="/" className="text-sm text-slate-500 hover:underline">
            ← LifeTracker
          </Link>
          <h1 className="text-2xl font-semibold">Food</h1>
        </div>
        <button type="button" className="btn-primary" onClick={() => setAdding(true)}>
          Log a meal
        </button>
      </div>

      <section className="mt-6" aria-busy={loading}>
        {error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <p>Couldn&apos;t load meals: {error}</p>
            <button type="button" className="mt-2 underline" onClick={reload}>
              Try again
            </button>
          </div>
        ) : !data ? (
          <div className="space-y-3" aria-label="Loading">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-20 animate-pulse rounded-lg bg-slate-200" />
            ))}
          </div>
        ) : data.items.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-300 bg-white p-10 text-center">
            <p className="text-slate-500">No meals logged yet.</p>
            <button type="button" className="btn-primary mt-4" onClick={() => setAdding(true)}>
              Log a meal
            </button>
          </div>
        ) : (
          <div className={`space-y-8 ${loading ? "opacity-60" : ""}`}>
            {groupByDay(data.items, (m) => m.eaten_on).map(({ day, items: meals }) => (
              <div key={day}>
                <div className="mb-2 flex items-baseline justify-between">
                  <h2 className="text-sm font-semibold text-slate-700">{formatDayHeading(day)}</h2>
                  <span className="text-sm font-semibold">
                    {formatKcal(meals.reduce((sum, meal) => sum + meal.total_kcal, 0))}
                  </span>
                </div>
                <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
                  {meals.map((meal) => (
                    <li key={meal.id}>
                      <Link href={`/food/${meal.id}`} className="flex items-center gap-3 p-3 hover:bg-slate-50">
                        {meal.thumbnail_url ? (
                          <ApiImage path={meal.thumbnail_url} alt={`${MEAL_LABELS[meal.meal_type]} photo`} className="h-14 w-14 shrink-0 rounded-md object-cover" />
                        ) : (
                          <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-md bg-amber-50 text-2xl" aria-hidden>
                            🍽️
                          </span>
                        )}
                        <span className="min-w-0 flex-1">
                          <span className="block font-medium">{MEAL_LABELS[meal.meal_type]}</span>
                          <span className="block truncate text-sm text-slate-500">{summariseItems(meal.items)}</span>
                        </span>
                        <span className="shrink-0 text-sm font-medium">{formatKcal(meal.total_kcal)}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
            {data.total > data.items.length && (
              <p className="text-sm text-slate-500">
                Showing the latest {data.items.length} of {data.total} meals.
              </p>
            )}
          </div>
        )}
      </section>

      {adding && (
        <Modal title="Log a meal" size="lg" onClose={() => setAdding(false)}>
          <MealForm
            submitLabel="Save meal"
            onCancel={() => setAdding(false)}
            onSubmit={async (values) => {
              await createMeal(values);
              setAdding(false);
              reload();
            }}
          />
        </Modal>
      )}
    </main>
  );
}
