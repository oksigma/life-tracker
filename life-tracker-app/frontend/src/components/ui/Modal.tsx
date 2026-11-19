"use client";

import { useEffect, useRef, type ReactNode } from "react";

type ModalProps = {
  title: string;
  /** "lg" for longer forms. */
  size?: "md" | "lg";
  onClose: () => void;
  children: ReactNode;
};

/** Accessible modal built on the native <dialog> element. Render it only while open. */
export function Modal({ title, size = "md", onClose, children }: ModalProps) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    dialog?.showModal();
    return () => dialog?.close();
  }, []);

  return (
    <dialog
      ref={ref}
      aria-label={title}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target === ref.current) onClose();
      }}
      className={`m-auto max-h-[calc(100dvh-2rem)] w-[calc(100%-2rem)] overflow-y-auto overscroll-contain ${size === "lg" ? "max-w-2xl" : "max-w-lg"} rounded-xl p-0 shadow-xl backdrop:bg-slate-900/40`}
    >
      <div className="p-4 sm:p-6">
        <h2 className="text-lg font-semibold">{title}</h2>
        <div className="mt-4">{children}</div>
      </div>
    </dialog>
  );
}
