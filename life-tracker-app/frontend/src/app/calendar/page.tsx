import type { Metadata } from "next";
import { CalendarView } from "@/features/calendar/components/CalendarView";
import { DAY_PATTERN, MONTH_PATTERN, monthOf } from "@/features/calendar/utils";

export const metadata: Metadata = { title: "Calendar · LifeTracker" };

type SearchParams = Promise<{ month?: string; day?: string }>;

export default async function CalendarPage({ searchParams }: { searchParams: SearchParams }) {
  const { month, day } = await searchParams;
  const validDay = day && DAY_PATTERN.test(day) ? day : null;
  const validMonth = month && MONTH_PATTERN.test(month) ? month : validDay ? monthOf(validDay) : null;
  // No month in the URL: let the browser pick the current month in the user's own time zone.
  return <CalendarView key={`${validMonth}|${validDay}`} initialMonth={validMonth} initialDay={validDay} />;
}
