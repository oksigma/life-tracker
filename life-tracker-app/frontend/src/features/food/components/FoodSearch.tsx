"use client";

import { useState } from "react";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { useLoader } from "@/hooks/useLoader";
import { errorMessage } from "@/lib/api";
import type { FoodOption } from "@/types/food";
import { lookupFood, searchMyFoods } from "../api";

type FoodSearchProps = {
  onPick: (food: FoodOption) => void;
  onManual: (name: string) => void;
};

type Lookup = { query: string; results?: FoodOption[]; error?: string; loading: boolean };

/**
 * "My foods" are searched as you type (local, unlimited). The food database is only searched when
 * asked, because Open Food Facts allows 10 searches a minute.
 */
export function FoodSearch({ onPick, onManual }: FoodSearchProps) {
  const [text, setText] = useState("");
  const query = useDebouncedValue(text.trim(), 200);
  const mine = useLoader(`mine|${query}`, () => searchMyFoods(query));
  const [lookup, setLookup] = useState<Lookup | null>(null);

  async function searchDatabase() {
    const q = text.trim();
    if (q.length < 2) return;
    setLookup({ query: q, loading: true });
    try {
      const { results } = await lookupFood(q);
      setLookup({ query: q, results, loading: false });
    } catch (e) {
      setLookup({ query: q, error: errorMessage(e), loading: false });
    }
  }

  function pick(food: FoodOption) {
    onPick(food);
    setText("");
    setLookup(null);
  }

  const showLookup = lookup && lookup.query === text.trim();

  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <label htmlFor="food-search" className="mb-1 block text-sm font-medium text-slate-700">
        Add a food
      </label>
      <div className="flex gap-2">
        <input
          id="food-search"
          className="input"
          placeholder="e.g. banana, toast, cheddar"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              void searchDatabase();
            }
          }}
          autoComplete="off"
        />
      </div>

      {(mine.data?.length ?? 0) > 0 && (
        <OptionList title={query ? "My foods" : "My most-used foods"} options={mine.data!} onPick={pick} />
      )}

      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          className="btn-secondary"
          disabled={text.trim().length < 2 || lookup?.loading}
          onClick={searchDatabase}
        >
          {lookup?.loading ? "Searching…" : "Search food database"}
        </button>
        <button
          type="button"
          className="btn-secondary"
          disabled={!text.trim()}
          onClick={() => {
            onManual(text.trim());
            setText("");
            setLookup(null);
          }}
        >
          Enter calories myself
        </button>
      </div>

      {showLookup && lookup.error && <p className="mt-2 text-sm text-red-600">{lookup.error}</p>}
      {showLookup && lookup.results && (
        lookup.results.length > 0 ? (
          <OptionList title="Food database results" options={lookup.results} onPick={pick} />
        ) : (
          <p className="mt-2 text-sm text-slate-500">
            No results with calorie data. Try other words, or enter the calories yourself.
          </p>
        )
      )}
      <p className="mt-3 text-xs text-slate-400">
        Food data from{" "}
        <a href="https://world.openfoodfacts.org" target="_blank" rel="noreferrer" className="underline">
          Open Food Facts
        </a>{" "}
        (ODbL). Calories are estimates.
      </p>
    </div>
  );
}

function OptionList({ title, options, onPick }: { title: string; options: FoodOption[]; onPick: (f: FoodOption) => void }) {
  return (
    <div className="mt-3">
      <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">{title}</p>
      <ul className="max-h-56 divide-y divide-slate-100 overflow-y-auto rounded-md border border-slate-200 bg-white">
        {options.map((food, i) => (
          <li key={`${food.off_code ?? food.name}-${i}`}>
            <button
              type="button"
              className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm hover:bg-slate-50"
              onClick={() => onPick(food)}
            >
              <span className="min-w-0">
                <span className="block truncate font-medium">{food.name}</span>
                {food.brand && <span className="block truncate text-xs text-slate-500">{food.brand}</span>}
              </span>
              <span className="shrink-0 text-right text-xs text-slate-600">
                {food.kcal_per_100g !== null && <span className="block">{Math.round(food.kcal_per_100g)} kcal/100g</span>}
                {food.kcal_per_serving !== null && (
                  <span className="block">
                    {Math.round(food.kcal_per_serving)} kcal/serving{food.serving_size ? ` (${food.serving_size})` : ""}
                  </span>
                )}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
