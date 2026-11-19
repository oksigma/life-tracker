// Empty by default: requests go to /api on this site and Next.js forwards them to the backend
// (see next.config.mjs). Set NEXT_PUBLIC_API_URL only to call a backend directly.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

/** Absolute URL for a backend path, e.g. for <img src>. */
export function apiUrl(path: string): string {
  return `${API_URL}${path}`;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type FastApiValidationError = { loc: (string | number)[]; msg: string };

function describeError(status: number, body: unknown): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return (detail as FastApiValidationError[])
      .map((e) => `${e.loc.filter((part) => part !== "body").join(".")}: ${e.msg}`)
      .join("; ");
  }
  return `Request failed (${status})`;
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    // Only JSON bodies (strings from JSON.stringify) get a JSON Content-Type. Anything else —
    // FormData file uploads in particular — must let the browser set the Content-Type itself,
    // or the multipart boundary is lost and the server sees no fields. Requests without a body
    // get no Content-Type, which also avoids an unnecessary CORS preflight on every GET.
    const isJson = typeof init?.body === "string";
    res = await fetch(apiUrl(path), {
      ...init,
      headers: { ...(isJson ? { "Content-Type": "application/json" } : {}), ...init?.headers },
    });
  } catch {
    throw new ApiError(0, "Can't reach the server. Is the backend running?");
  }
  if (res.status === 401 && !path.startsWith("/api/auth/")) redirectToLogin();
  if (res.status === 204) return undefined as T;
  const body: unknown = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, describeError(res.status, body));
  return body as T;
}

/** Send the browser to the login page, coming back to the current page afterwards. */
export function redirectToLogin(): void {
  if (typeof window === "undefined" || window.location.pathname === "/login") return;
  const next = window.location.pathname + window.location.search;
  // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- full reload clears signed-in state
  window.location.assign(`/login?next=${encodeURIComponent(next)}`);
}

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong";
}
