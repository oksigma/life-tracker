"use client";

import Link from "next/link";
import { useState } from "react";
import { ApiImage } from "@/components/ui/ApiImage";
import { Modal } from "@/components/ui/Modal";
import { formatDayHeading } from "@/lib/dates";
import { uploadOutfit } from "../api";
import { useOutfits } from "../hooks/useOutfits";
import { groupByDay } from "@/lib/grouping";
import { OutfitForm } from "./OutfitForm";

export function OutfitsView() {
  const [version, setVersion] = useState(0);
  const { data, error, loading } = useOutfits(version);
  const [adding, setAdding] = useState(false);
  const reload = () => setVersion((v) => v + 1);

  return (
    <main className="mx-auto max-w-5xl px-4 pb-28 pt-6 sm:pb-8 sm:pt-8">
      <div className="flex items-center justify-between gap-4">
        <div>
          <Link href="/" className="text-sm text-slate-500 hover:underline">
            ← LifeTracker
          </Link>
          <h1 className="text-2xl font-semibold">Clothing</h1>
        </div>
        <button type="button" className="btn-primary hidden sm:inline-flex" onClick={() => setAdding(true)}>
          Log an outfit
        </button>
      </div>

      {/* On phones: a thumb-reachable floating button instead of the header button. */}
      <button
        type="button"
        onClick={() => setAdding(true)}
        aria-label="Log an outfit"
        className="fixed bottom-[calc(1.25rem+env(safe-area-inset-bottom))] right-5 z-20 flex h-14 w-14 items-center justify-center rounded-full bg-slate-900 text-3xl leading-none text-white shadow-lg active:scale-95 sm:hidden"
      >
        +
      </button>

      <section className="mt-4 sm:mt-6" aria-busy={loading}>
        {error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <p>Couldn&apos;t load outfits: {error}</p>
            <button type="button" className="mt-2 underline" onClick={reload}>
              Try again
            </button>
          </div>
        ) : !data ? (
          <GallerySkeleton />
        ) : data.items.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-300 bg-white p-10 text-center">
            <p className="text-slate-500">No outfits logged yet.</p>
            <button type="button" className="btn-primary mt-4" onClick={() => setAdding(true)}>
              Log an outfit
            </button>
          </div>
        ) : (
          <div className={`space-y-4 sm:space-y-6 ${loading ? "opacity-60" : ""}`}>
            {groupByDay(data.items, (o) => o.worn_on).map(({ day, items: outfits }) => (
              <div key={day}>
                <h2 className="sticky top-0 z-10 -mx-4 mb-2 bg-slate-50/95 px-4 py-2 text-sm font-semibold text-slate-700 backdrop-blur">
                  {formatDayHeading(day)}
                </h2>
                <ul className="grid grid-cols-3 gap-2 sm:grid-cols-4 sm:gap-3 md:grid-cols-5 lg:grid-cols-6">
                  {outfits.map((outfit) => (
                    <li key={outfit.id}>
                      <Link
                        href={`/clothing/${outfit.id}`}
                        className="group block overflow-hidden rounded-md border border-slate-200 bg-white"
                      >
                        <ApiImage
                          path={outfit.thumbnail_url}
                          alt={outfit.notes ?? `Outfit worn ${formatDayHeading(day)}`}
                          className="aspect-[3/4] w-full object-cover transition group-hover:opacity-90"
                        />
                        {outfit.notes && <p className="truncate px-2 py-1 text-xs text-slate-600">{outfit.notes}</p>}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
            {data.total > data.items.length && (
              <p className="text-sm text-slate-500">
                Showing the latest {data.items.length} of {data.total} outfits.
              </p>
            )}
          </div>
        )}
      </section>

      {adding && (
        <Modal title="Log an outfit" onClose={() => setAdding(false)}>
          <OutfitForm
            submitLabel="Save outfit"
            onCancel={() => setAdding(false)}
            onSubmit={async ({ photo, wornOn, notes }) => {
              if (!photo) return;
              await uploadOutfit(photo, wornOn, notes);
              setAdding(false);
              reload();
            }}
          />
        </Modal>
      )}
    </main>
  );
}

function GallerySkeleton() {
  return (
    <div aria-label="Loading">
      <div className="mb-3 h-4 w-40 animate-pulse rounded bg-slate-200" />
      <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 sm:gap-3 md:grid-cols-5 lg:grid-cols-6">
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="aspect-[3/4] animate-pulse rounded-md bg-slate-200" />
        ))}
      </div>
    </div>
  );
}
