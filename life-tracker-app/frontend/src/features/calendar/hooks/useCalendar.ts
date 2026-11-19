import { useLoader } from "@/hooks/useLoader";
import type { CalendarRange, DayEntries } from "@/types/calendar";
import { getCalendarRange, getDayEntries } from "../api";

export function useCalendarRange(start: string, end: string, version: number) {
  return useLoader<CalendarRange>(`${version}|${start}|${end}`, () => getCalendarRange(start, end));
}

export function useDayEntries(day: string, version: number) {
  return useLoader<DayEntries>(`${version}|${day}`, () => getDayEntries(day));
}
