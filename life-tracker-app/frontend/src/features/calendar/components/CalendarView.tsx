"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { formatDayHeading, todayLocal } from "@/lib/dates";
import type { CalendarDay } from "@/types/calendar";
import { CALENDAR_AREAS, describeCounts } from "../areas";
import { useCalendarRange } from "../hooks/useCalendar";
import { addMonths, formatMonth, monthGrid, monthOf, weekdayNames, type MonthKey } from "../utils";
import { DayPanel } from "./DayPanel";

type CalendarViewProps = {
  /** null = the current month. */
  initialMonth: MonthKey | null;
  initialDay: string | null;
};

export function CalendarView({ initialMonth, initialDay }: CalendarViewProps) {
  const today = todayLocal();
  const [month, setMonth] = useState<MonthKey>(initialMonth ?? monthOf(today));
  const [selected, setSelected] = useState<string | null>(initialDay);
  const [version, setVersion] = useState(0);
  const grid = useMemo(() => monthGrid(month), [month]);
  const { data, error, loading } = useCalendarRange(grid.start, grid.end, version);

  const byDate = useMemo(() => {
    const map = new Map<string, CalendarDay["counts"]>();
    for (const day of data?.days ?? []) map.set(day.date, day.counts);
    return map;
  }, [data]);
  const loggedThisMonth = (data?.days ?? []).some((d) => monthOf(d.date) === month);

  // Keep month/day in the URL so reload, links and the back button return to the same view.
  useEffect(() => {
    const params = new URLSearchParams({ month });
    if (selected) params.set("day", selected);
    window.history.replaceState(null, "", `?${params}`);
  }, [month, selected]);

  function goToMonth(next: MonthKey) {
    setMonth(next);
    if (selected && monthOf(selected) !== next) setSelected(null);
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <Link href="/" className="text-sm text-slate-500 hover:underline">
        ← LifeTracker
      </Link>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Calendar</h1>
        <div className="flex items-center gap-2">
          <button type="button" className="btn-secondary px-3" onClick={() => goToMonth(addMonths(month, -1))} aria-label="Previous month">
            ←
          </button>
          <h2 className="min-w-40 text-center font-medium" aria-live="polite">
            {formatMonth(month)}
          </h2>
          <button type="button" className="btn-secondary px-3" onClick={() => goToMonth(addMonths(month, 1))} aria-label="Next month">
            →
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => {
              setMonth(monthOf(today));
              setSelected(today);
            }}
          >
            Today
          </button>
        </div>
      </div>

      <Legend />

      <div className="mt-4 grid gap-6 lg:grid-cols-[1fr_20rem]">
        <section aria-busy={loading}>
          {error && (
            <div className="mb-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              Couldn&apos;t load the calendar: {error}{" "}
              <button type="button" className="underline" onClick={() => setVersion((v) => v + 1)}>
                Try again
              </button>
            </div>
          )}
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white" role="grid" aria-label={formatMonth(month)}>
            <div className="grid grid-cols-7 border-b border-slate-200 bg-slate-50 text-center text-xs font-medium text-slate-500" role="row">
              {weekdayNames().map((name) => (
                <div key={name} className="py-2" role="columnheader">
                  {name}
                </div>
              ))}
            </div>
            {grid.weeks.map((week) => (
              <div key={week[0]} className="grid grid-cols-7" role="row">
                {week.map((day) => (
                  <DayCell
                    key={day}
                    day={day}
                    counts={byDate.get(day)}
                    inMonth={monthOf(day) === month}
                    isToday={day === today}
                    isFuture={day > today}
                    isSelected={day === selected}
                    dimmed={loading}
                    onSelect={() => setSelected(day)}
                  />
                ))}
              </div>
            ))}
          </div>
          {data && !loading && !loggedThisMonth && (
            <p className="mt-3 text-sm text-slate-500">Nothing logged in {formatMonth(month)}.</p>
          )}
        </section>

        <aside>
          {selected ? (
            <DayPanel day={selected} hasEntries={!!byDate.get(selected)} version={version} />
          ) : (
            <div className="rounded-lg border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-500">
              Select a day to see what you logged.
            </div>
          )}
        </aside>
      </div>
    </main>
  );
}

function Legend() {
  return (
    <ul className="mt-4 flex flex-wrap gap-2 text-sm" aria-label="Legend">
      {CALENDAR_AREAS.map((area) => (
        <li key={area.key} className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 ring-1 ${area.chipClass}`}>
          <span aria-hidden>{area.symbol}</span>
          {area.label}
        </li>
      ))}
    </ul>
  );
}

type DayCellProps = {
  day: string;
  counts: CalendarDay["counts"] | undefined;
  inMonth: boolean;
  isToday: boolean;
  isFuture: boolean;
  isSelected: boolean;
  dimmed: boolean;
  onSelect: () => void;
};

function DayCell({ day, counts, inMonth, isToday, isFuture, isSelected, dimmed, onSelect }: DayCellProps) {
  const summary = counts ? describeCounts(counts) : "nothing logged";
  const muted = !inMonth || isFuture;
  return (
    <button
      type="button"
      role="gridcell"
      aria-selected={isSelected}
      aria-label={`${formatDayHeading(day)}: ${summary}`}
      onClick={onSelect}
      className={[
        "relative flex min-h-16 flex-col items-start gap-1 border-b border-r border-slate-100 p-1.5 text-left transition sm:min-h-24 sm:p-2",
        "hover:bg-slate-50 focus-visible:z-10 focus-visible:outline-2 focus-visible:outline-slate-500",
        isSelected ? "bg-slate-100" : "",
        muted ? "text-slate-400" : "text-slate-800",
        dimmed ? "opacity-60" : "",
      ].join(" ")}
    >
      <span
        className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium sm:text-sm ${isToday ? "bg-slate-900 text-white" : ""}`}
      >
        {Number(day.slice(8))}
      </span>
      {counts && (
        <span className="flex flex-wrap gap-0.5 sm:gap-1">
          {CALENDAR_AREAS.filter((area) => counts[area.key]).map((area) => (
            <span
              key={area.key}
              className={`inline-flex items-center rounded px-0.5 text-xs leading-5 ring-1 sm:px-1 ${area.chipClass} ${muted ? "opacity-60" : ""}`}
            >
              <span aria-hidden>{area.symbol}</span>
              {counts[area.key]! > 1 && <span className="ml-0.5 font-semibold">{counts[area.key]}</span>}
            </span>
          ))}
        </span>
      )}
    </button>
  );
}
