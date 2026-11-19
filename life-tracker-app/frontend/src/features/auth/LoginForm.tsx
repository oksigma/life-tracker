"use client";

import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { errorMessage } from "@/lib/api";
import { safeNextPath, signIn } from "@/lib/auth";

export function LoginForm() {
  const next = safeNextPath(useSearchParams().get("next"));
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!password) return;
    setBusy(true);
    setError(null);
    try {
      await signIn(password);
      // Full navigation so every page reloads its data with the new cookie.
      window.location.assign(next);
    } catch (e) {
      setError(errorMessage(e));
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="mt-6 space-y-4">
      <div>
        <label htmlFor="password" className="block text-sm font-medium">
          Password
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          autoFocus
          className="input mt-1"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          aria-invalid={!!error}
          aria-describedby={error ? "password-error" : undefined}
        />
        {error && (
          <p id="password-error" className="mt-1 text-sm text-red-600">
            {error}
          </p>
        )}
      </div>
      <button type="submit" className="btn-primary w-full" disabled={busy || !password}>
        {busy ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
