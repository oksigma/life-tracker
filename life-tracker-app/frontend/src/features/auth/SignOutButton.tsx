"use client";

import { useEffect, useState } from "react";
import { redirectToLogin } from "@/lib/api";
import { getAuthStatus, signOut } from "@/lib/auth";

/**
 * Shown only when the app has a password (deployed); hidden in local development.
 * The home page loads no other data, so this also sends a signed-out visitor to the login page.
 */
export function SignOutButton() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    getAuthStatus()
      .then((status) => {
        if (status.required && !status.signed_in) redirectToLogin();
        setShow(status.required && status.signed_in);
      })
      .catch(() => setShow(false));
  }, []);

  if (!show) return null;
  return (
    <button
      type="button"
      className="text-sm text-slate-500 hover:underline"
      onClick={async () => {
        await signOut().catch(() => undefined);
        // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- full reload clears signed-in state
        window.location.assign("/login");
      }}
    >
      Sign out
    </button>
  );
}
