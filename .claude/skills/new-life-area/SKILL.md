---
name: new-life-area
description: Scaffold a new life area (e.g. "sleep", "books") across the frontend and the Python backend.
argument-hint: <area name>
disable-model-invocation: true
---

Add a new life area called: $ARGUMENTS (lowercase, single word)

1. Add it to `LIFE_AREAS` in `life-tracker-app/frontend/src/types/life-area.ts`.
2. Create `life-tracker-app/frontend/src/features/<area>/components/` and `life-tracker-app/frontend/src/app/<area>/page.tsx`, following an existing area.
3. Create `life-tracker-app/backend/app/modules/<area>/` with `__init__.py` and a README following an existing module. If other modules have routers included in `app/api/router.py`, add a router for this one too.
4. Add its collection(s) to `life-tracker-app/database/schema.md`.
5. Register it on the calendar: add `count_by_day`/`list_on_day` to its repository and service, add it to `CalendarService` and `DayEntries` in `backend/app/modules/calendar/`, to `CalendarAreaKey` in `frontend/src/types/calendar.ts`, and to `CALENDAR_AREAS` in `frontend/src/features/calendar/areas.ts` with its symbol and colour.
6. Add the area to the table in `docs/product/features.md`.
7. Offer to start a spec for it with `/new-spec`.
