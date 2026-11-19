"use client";

import { UNITS, type Unit } from "@/types/food";
import { canCalculate, draftError, draftKcal, formatKcal, UNIT_LABELS, unitsFor, type DraftItem } from "../utils";

type ItemsEditorProps = {
  items: DraftItem[];
  onChange: (items: DraftItem[]) => void;
  showErrors: boolean;
};

export function ItemsEditor({ items, onChange, showErrors }: ItemsEditorProps) {
  if (items.length === 0) return <p className="text-sm text-slate-500">No foods added yet.</p>;

  const update = (key: string, changes: Partial<DraftItem>) =>
    onChange(items.map((item) => (item.key === key ? { ...item, ...changes } : item)));
  const remove = (key: string) => onChange(items.filter((item) => item.key !== key));
  const total = items.reduce((sum, item) => sum + (draftKcal(item) ?? 0), 0);

  return (
    <div>
      <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200">
        {items.map((item) => {
          const calculable = canCalculate(item);
          const kcal = draftKcal(item);
          const error = showErrors ? draftError(item) : null;
          const units: Unit[] = item.source === "manual" ? [...UNITS] : unitsFor(item);
          return (
            <li key={item.key} className="p-3">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  {item.source === "manual" ? (
                    <input
                      className="input py-1"
                      aria-label="Food name"
                      value={item.name}
                      maxLength={200}
                      onChange={(e) => update(item.key, { name: e.target.value })}
                    />
                  ) : (
                    <>
                      <p className="truncate font-medium">{item.name}</p>
                      {item.brand && <p className="truncate text-xs text-slate-500">{item.brand}</p>}
                    </>
                  )}
                </div>
                <button
                  type="button"
                  className="shrink-0 rounded px-2 py-1 text-sm text-red-600 hover:bg-red-50"
                  onClick={() => remove(item.key)}
                  aria-label={`Remove ${item.name || "food"}`}
                >
                  Remove
                </button>
              </div>

              <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
                <input
                  type="number"
                  inputMode="decimal"
                  min="0"
                  step="any"
                  className="input w-24 py-1"
                  aria-label="Amount"
                  placeholder="Amount"
                  value={item.quantity}
                  onChange={(e) => update(item.key, { quantity: e.target.value })}
                />
                <select
                  className="input w-32 py-1"
                  aria-label="Unit"
                  value={item.unit}
                  onChange={(e) => update(item.key, { unit: e.target.value as Unit | "" })}
                >
                  {item.source === "manual" && <option value="">—</option>}
                  {units.map((unit) => (
                    <option key={unit} value={unit}>
                      {UNIT_LABELS[unit]}
                    </option>
                  ))}
                </select>
                {calculable ? (
                  <span className="ml-auto font-medium">{kcal !== null ? formatKcal(kcal) : "—"}</span>
                ) : (
                  <label className="ml-auto flex items-center gap-1">
                    <input
                      type="number"
                      inputMode="decimal"
                      min="0"
                      step="any"
                      className="input w-24 py-1"
                      aria-label="Calories"
                      placeholder="kcal"
                      value={item.kcal}
                      onChange={(e) => update(item.key, { kcal: e.target.value })}
                    />
                    kcal
                  </label>
                )}
              </div>
              {item.serving_size && item.unit === "serving" && (
                <p className="mt-1 text-xs text-slate-500">1 serving = {item.serving_size}</p>
              )}
              {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
            </li>
          );
        })}
      </ul>
      <p className="mt-2 text-right font-semibold">Total {formatKcal(total)}</p>
    </div>
  );
}
