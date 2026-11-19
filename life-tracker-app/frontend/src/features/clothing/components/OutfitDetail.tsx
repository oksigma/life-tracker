"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ApiImage } from "@/components/ui/ApiImage";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Modal } from "@/components/ui/Modal";
import { formatDayHeading } from "@/lib/dates";
import { deleteOutfit, updateOutfit } from "../api";
import { useOutfit } from "../hooks/useOutfits";
import { OutfitForm } from "./OutfitForm";

export function OutfitDetail({ id }: { id: string }) {
  const router = useRouter();
  const [version, setVersion] = useState(0);
  const { data: outfit, error } = useOutfit(id, version);
  const [dialog, setDialog] = useState<"edit" | "delete" | null>(null);
  const close = () => setDialog(null);
  const notFound = error === "Outfit not found";

  return (
    <main className="mx-auto max-w-2xl px-4 py-6 sm:py-8">
      <Link href="/clothing" className="text-sm text-slate-500 hover:underline">
        ← All outfits
      </Link>

      {error ? (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <p>{notFound ? "This outfit doesn't exist." : `Couldn't load outfit: ${error}`}</p>
          {!notFound && (
            <button type="button" className="mt-2 underline" onClick={() => setVersion((v) => v + 1)}>
              Try again
            </button>
          )}
        </div>
      ) : !outfit || outfit.id !== id ? (
        <div className="mt-4 h-[50vh] animate-pulse rounded-lg bg-slate-200 sm:h-[60vh]" aria-label="Loading" />
      ) : (
        <article className="mt-4 overflow-hidden rounded-lg border border-slate-200 bg-white">
          <ApiImage
            path={outfit.photo_url}
            alt={outfit.notes ?? "Outfit"}
            loading="eager"
            className="max-h-[50vh] w-full bg-slate-100 object-contain sm:max-h-[60vh]"
          />
          <div className="flex flex-col gap-4 p-4 sm:flex-row sm:items-start sm:justify-between sm:p-6">
            <div>
              <h1 className="text-lg font-semibold sm:text-xl">{formatDayHeading(outfit.worn_on)}</h1>
              {outfit.notes && <p className="mt-2 whitespace-pre-wrap text-slate-700">{outfit.notes}</p>}
            </div>
            <div className="flex shrink-0 gap-2">
              <button type="button" className="btn-secondary flex-1 sm:flex-none" onClick={() => setDialog("edit")}>
                Edit
              </button>
              <button type="button" className="btn-danger flex-1 sm:flex-none" onClick={() => setDialog("delete")}>
                Delete
              </button>
            </div>
          </div>

          {dialog === "edit" && (
            <Modal title="Edit outfit" onClose={close}>
              <OutfitForm
                initial={outfit}
                submitLabel="Save changes"
                onCancel={close}
                onSubmit={async ({ wornOn, notes }) => {
                  await updateOutfit(outfit.id, { worn_on: wornOn, notes });
                  close();
                  setVersion((v) => v + 1);
                }}
              />
            </Modal>
          )}

          {dialog === "delete" && (
            <ConfirmDialog
              title="Delete outfit?"
              message={`This outfit and its photo from ${formatDayHeading(outfit.worn_on)} will be permanently deleted.`}
              confirmLabel="Delete"
              onClose={close}
              onConfirm={async () => {
                await deleteOutfit(outfit.id);
                router.push("/clothing");
              }}
            />
          )}
        </article>
      )}
    </main>
  );
}
