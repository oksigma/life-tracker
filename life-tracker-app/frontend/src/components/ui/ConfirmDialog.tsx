"use client";

import { useState } from "react";
import { errorMessage } from "@/lib/api";
import { Modal } from "./Modal";

type ConfirmDialogProps = {
  title: string;
  message: string;
  confirmLabel: string;
  onConfirm: () => Promise<void>;
  onClose: () => void;
};

export function ConfirmDialog({ title, message, confirmLabel, onConfirm, onClose }: ConfirmDialogProps) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function confirm() {
    setBusy(true);
    setError(null);
    try {
      await onConfirm();
    } catch (e) {
      setError(errorMessage(e));
      setBusy(false);
    }
  }

  return (
    <Modal title={title} onClose={onClose}>
      <p className="text-slate-600">{message}</p>
      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      <div className="mt-6 flex justify-end gap-2">
        <button type="button" onClick={onClose} className="btn-secondary">
          Cancel
        </button>
        <button type="button" onClick={confirm} disabled={busy} className="btn-danger">
          {busy ? "Deleting…" : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}
