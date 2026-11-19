import { useEffect, useState } from "react";
import { errorMessage } from "@/lib/api";

type Result<T> = { key: string; data?: T; error?: string };

/**
 * Loads data for `key`, keeping the previous data visible while a new request is in flight.
 * Include a version counter in `key` and bump it to reload.
 */
export function useLoader<T>(key: string, load: () => Promise<T>) {
  const [result, setResult] = useState<Result<T>>({ key: "" });

  useEffect(() => {
    let cancelled = false;
    load().then(
      (data) => !cancelled && setResult({ key, data }),
      (error) => !cancelled && setResult({ key, error: errorMessage(error) }),
    );
    return () => {
      cancelled = true;
    };
    // `load` is recreated each render; `key` captures everything it depends on.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  const loading = result.key !== key;
  return { data: result.data, error: loading ? undefined : result.error, loading };
}
