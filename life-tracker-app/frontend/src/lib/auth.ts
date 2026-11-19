import { api } from "@/lib/api";

export type AuthStatus = { required: boolean; signed_in: boolean };

export function getAuthStatus(): Promise<AuthStatus> {
  return api<AuthStatus>("/api/auth/status");
}

export function signIn(password: string): Promise<void> {
  return api<void>("/api/auth/login", { method: "POST", body: JSON.stringify({ password }) });
}

export function signOut(): Promise<void> {
  return api<void>("/api/auth/logout", { method: "POST" });
}

/** Only allow redirects to pages on this site (no "//evil.com" or absolute URLs). */
export function safeNextPath(next: string | null): string {
  return next && next.startsWith("/") && !next.startsWith("//") && !next.startsWith("/\\") ? next : "/";
}
