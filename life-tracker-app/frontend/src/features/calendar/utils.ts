import { parseIsoDate, toIsoDate } from "@/lib/dates";

/** A month as "YYYY-MM". */
export type MonthKey = string;

export const MONTH_PATTERN = /^\d{4}-(0[1-9]|1[0-2])$/;
export const DAY_PATTERN = /^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/;

export function monthOf(isoDate: string): MonthKey {
  return isoDate.slice(0, 7);
}

export function addMonths(month: MonthKey, delta: number): MonthKey {
  const [year, m] = month.split("-").map(Number);
  return toIsoDate(new Date(year, m - 1 + delta, 1)).slice(0, 7);
}

export function formatMonth(month: MonthKey): string {
  return parseIsoDate(`${month}-01`).toLocaleDateString(undefined, { month: "long", year: "numeric" });
}

/**
 * The days to show for a month: whole weeks (Monday first) covering the month,
 * including the trailing/leading days of neighbouring months.
 */
export function monthGrid(month: MonthKey): { start: string; end: string; weeks: string[][] } {
  const [year, m] = month.split("-").map(Number);
  const first = new Date(year, m - 1, 1);
  const last = new Date(year, m, 0);
  const lead = (first.getDay() + 6) % 7; // days before the 1st, Monday = 0
  const trail = (7 - ((last.getDay() + 6) % 7) - 1) % 7;
  const cursor = new Date(year, m - 1, 1 - lead);
  const total = lead + last.getDate() + trail;

  const weeks: string[][] = [];
  for (let i = 0; i < total; i++) {
    if (i % 7 === 0) weeks.push([]);
    weeks[weeks.length - 1].push(toIsoDate(cursor));
    cursor.setDate(cursor.getDate() + 1);
  }
  return { start: weeks[0][0], end: weeks.at(-1)!.at(-1)!, weeks };
}

/** Short weekday names, Monday first, in the user's locale. */
export function weekdayNames(): string[] {
  // 2024-01-01 was a Monday.
  return Array.from({ length: 7 }, (_, i) =>
    new Date(2024, 0, 1 + i).toLocaleDateString(undefined, { weekday: "short" }),
  );
}
