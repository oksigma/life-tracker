/** A Date's local calendar date as YYYY-MM-DD (never via UTC, which can shift the day). */
export function toIsoDate(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

/** Today's date in the user's local time zone, as YYYY-MM-DD. */
export function todayLocal(): string {
  return toIsoDate(new Date());
}

/** Parse YYYY-MM-DD as a local-midnight Date. */
export function parseIsoDate(isoDate: string): Date {
  const [year, month, day] = isoDate.split("-").map(Number);
  return new Date(year, month - 1, day);
}

/** Format a YYYY-MM-DD calendar date, e.g. "14 Nov 2026". */
export function formatDate(isoDate: string): string {
  return parseIsoDate(isoDate).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

/** Format a YYYY-MM-DD calendar date as a heading, e.g. "Saturday 14 November 2026". */
export function formatDayHeading(isoDate: string): string {
  if (isoDate === todayLocal()) return "Today";
  return parseIsoDate(isoDate).toLocaleDateString(undefined, {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}
