"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ApiImage } from "@/components/ui/ApiImage";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Modal } from "@/components/ui/Modal";
import { formatDayHeading } from "@/lib/dates";
import { deleteMeal, updateMeal } from "../api";
import { useMeal } from "../hooks/useMeals";
import { describeAmount, formatKcal, MEAL_LABELS } from "../utils";
import { MealForm } from "./MealForm";

export function MealDetail({ id }: { id: string }) {
  const router = useRouter();
  const [version, setVersion] = useState(0);
  const { data: meal, error } = useMeal(id, version);
  const [dialog, setDialog] = useState<"edit" | "delete" | null>(null);
  const close = () => setDialog(null);
  const notFound = error === "Meal not found";

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <Link href="/food" className="text-sm text-slate-500 hover:underline">
        ← All meals
      </Link>

      {error ? (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <p>{notFound ? "This meal doesn't exist." : `Couldn't load meal: ${error}`}</p>
          {!notFound && (
            <button type="button" className="mt-2 underline" onClick={() => setVersion((v) => v + 1)}>
              Try again
            </button>
          )}
        </div>
      ) : !meal || meal.id !== id ? (
        <div className="mt-4 h-64 animate-pulse rounded-lg bg-slate-200" aria-label="Loading" />
      ) : (
        <article className="mt-4 overflow-hidden rounded-lg border border-slate-200 bg-white">
          {meal.photo_url && (
            <ApiImage path={meal.photo_url} alt={`${MEAL_LABELS[meal.meal_type]} photo`} loading="eager" className="max-h-[60vh] w-full bg-slate-100 object-contain" />
          )}
          <div className="p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-xl font-semibold">{MEAL_LABELS[meal.meal_type]}</h1>
                <p className="text-slate-500">{formatDayHeading(meal.eaten_on)}</p>
              </div>
              <div className="flex shrink-0 gap-2">
                <button type="button" className="btn-secondary" onClick={() => setDialog("edit")}>
                  Edit
                </button>
                <button type="button" className="btn-danger" onClick={() => setDialog("delete")}>
                  Delete
                </button>
              </div>
            </div>

            {meal.items.length > 0 ? (
              <table className="mt-6 w-full text-sm">
                <thead className="text-left text-slate-500">
                  <tr>
                    <th className="pb-2 font-medium">Food</th>
                    <th className="pb-2 font-medium">Amount</th>
                    <th className="pb-2 text-right font-medium">Calories</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {meal.items.map((item, i) => (
                    <tr key={i}>
                      <td className="py-2">
                        {item.name}
                        {item.brand && <span className="block text-xs text-slate-500">{item.brand}</span>}
                      </td>
                      <td className="py-2 text-slate-600">{describeAmount(item) ?? "—"}</td>
                      <td className="py-2 text-right">{formatKcal(item.kcal)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t border-slate-200 font-semibold">
                    <td className="pt-2" colSpan={2}>
                      Total
                    </td>
                    <td className="pt-2 text-right">{formatKcal(meal.total_kcal)}</td>
                  </tr>
                </tfoot>
              </table>
            ) : (
              <p className="mt-6 text-sm text-slate-500">No foods added — edit the meal to add some.</p>
            )}

            {meal.notes && <p className="mt-6 whitespace-pre-wrap text-slate-700">{meal.notes}</p>}
          </div>

          {dialog === "edit" && (
            <Modal title="Edit meal" size="lg" onClose={close}>
              <MealForm
                initial={meal}
                submitLabel="Save changes"
                onCancel={close}
                onSubmit={async ({ eatenOn, mealType, notes, items }) => {
                  await updateMeal(meal.id, { eaten_on: eatenOn, meal_type: mealType, notes, items });
                  close();
                  setVersion((v) => v + 1);
                }}
              />
            </Modal>
          )}

          {dialog === "delete" && (
            <ConfirmDialog
              title="Delete meal?"
              message={`This ${MEAL_LABELS[meal.meal_type].toLowerCase()} from ${formatDayHeading(meal.eaten_on)}${meal.photo_url ? " and its photo" : ""} will be permanently deleted.`}
              confirmLabel="Delete"
              onClose={close}
              onConfirm={async () => {
                await deleteMeal(meal.id);
                router.push("/food");
              }}
            />
          )}
        </article>
      )}
    </main>
  );
}
