"use client";

import { useState, type FormEvent } from "react";
import { ApiImage } from "@/components/ui/ApiImage";
import { PhotoPicker } from "@/components/ui/PhotoPicker";
import { errorMessage } from "@/lib/api";
import { todayLocal } from "@/lib/dates";
import { MEAL_TYPES, type Meal, type MealItemInput, type MealType } from "@/types/food";
import {
  defaultMealType,
  draftError,
  draftFromItem,
  draftFromOption,
  manualDraft,
  MAX_ITEMS,
  MAX_NOTES,
  MEAL_LABELS,
  toItemInput,
  type DraftItem,
} from "../utils";
import { FoodSearch } from "./FoodSearch";
import { ItemsEditor } from "./ItemsEditor";

export type MealFormValues = {
  photo: File | null;
  eatenOn: string;
  mealType: MealType;
  notes: string | null;
  items: MealItemInput[];
};

type MealFormProps = {
  /** When given, edits this meal (the photo can't be changed). */
  initial?: Meal;
  submitLabel: string;
  onSubmit: (values: MealFormValues) => Promise<void>;
  onCancel: () => void;
};

export function MealForm({ initial, submitLabel, onSubmit, onCancel }: MealFormProps) {
  const isNew = !initial;
  const [photo, setPhoto] = useState<File | null>(null);
  const [eatenOn, setEatenOn] = useState(initial?.eaten_on ?? todayLocal());
  const [mealType, setMealType] = useState<MealType>(initial?.meal_type ?? defaultMealType());
  const [notes, setNotes] = useState(initial?.notes ?? "");
  const [items, setItems] = useState<DraftItem[]>(() => initial?.items.map(draftFromItem) ?? []);
  const [showErrors, setShowErrors] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const dateError = !eatenOn ? "Enter the date." : eatenOn > todayLocal() ? "The date can't be in the future." : null;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setShowErrors(true);
    if (dateError || items.some((item) => draftError(item)) || notes.length > MAX_NOTES) return;
    if (isNew && !photo && items.length === 0) {
      setFormError("Add a photo or at least one food.");
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      await onSubmit({ photo, eatenOn, mealType, notes: notes.trim() || null, items: items.map(toItemInput) });
    } catch (e) {
      setFormError(errorMessage(e));
      setSaving(false);
    }
  }

  const addItem = (item: DraftItem) => setItems((current) => (current.length < MAX_ITEMS ? [...current, item] : current));

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      {isNew ? (
        <PhotoPicker photo={photo} onChange={setPhoto} optional />
      ) : (
        initial.thumbnail_url && (
          <ApiImage path={initial.thumbnail_url} alt="Meal" className="h-28 w-28 rounded-lg object-cover" />
        )
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="meal-eaten-on" className="mb-1 block text-sm font-medium text-slate-700">
            Date
          </label>
          <input
            id="meal-eaten-on"
            type="date"
            className="input"
            value={eatenOn}
            max={todayLocal()}
            onChange={(e) => setEatenOn(e.target.value)}
            aria-invalid={showErrors && !!dateError}
          />
          {showErrors && dateError && <p className="mt-1 text-sm text-red-600">{dateError}</p>}
        </div>
        <div>
          <label htmlFor="meal-type" className="mb-1 block text-sm font-medium text-slate-700">
            Meal
          </label>
          <select id="meal-type" className="input" value={mealType} onChange={(e) => setMealType(e.target.value as MealType)}>
            {MEAL_TYPES.map((type) => (
              <option key={type} value={type}>
                {MEAL_LABELS[type]}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <p className="mb-1 text-sm font-medium text-slate-700">Foods</p>
        <ItemsEditor items={items} onChange={setItems} showErrors={showErrors} />
      </div>

      <FoodSearch onPick={(food) => addItem(draftFromOption(food))} onManual={(name) => addItem(manualDraft(name))} />

      <div>
        <label htmlFor="meal-notes" className="mb-1 block text-sm font-medium text-slate-700">
          Notes <span className="font-normal text-slate-400">(optional)</span>
        </label>
        <textarea
          id="meal-notes"
          className="input min-h-16"
          value={notes}
          maxLength={MAX_NOTES}
          onChange={(e) => setNotes(e.target.value)}
        />
      </div>

      {formError && <p className="text-sm text-red-600">{formError}</p>}

      <div className="flex justify-end gap-2 pt-2">
        <button type="button" onClick={onCancel} className="btn-secondary">
          Cancel
        </button>
        <button type="submit" disabled={saving} className="btn-primary">
          {saving ? "Saving…" : submitLabel}
        </button>
      </div>
    </form>
  );
}
