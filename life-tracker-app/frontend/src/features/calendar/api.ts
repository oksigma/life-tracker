import { api } from "@/lib/api";
import type { CalendarRange, DayEntries } from "@/types/calendar";

export function getCalendarRange(start: string, end: string): Promise<CalendarRange> {
  return api<CalendarRange>(`/api/calendar?start=${start}&end=${end}`);
}

export function getDayEntries(day: string): Promise<DayEntries> {
  return api<DayEntries>(`/api/calendar/days/${day}`);
}
