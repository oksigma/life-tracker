# Frontend

- Next.js App Router: routes in `src/app/<route>/page.tsx`. Prefer Server Components; add `"use client"` only when needed.
- Feature code lives in `src/features/<area>/` (components, hooks, API calls for that area). Pages stay thin.
- Life areas: clothing, health, movies, food, drinks. The list is in `src/types/life-area.ts`.
- Reusable UI primitives in `src/components/ui/`; layout pieces in `src/components/layout/`.
- Call the backend (FastAPI, `NEXT_PUBLIC_API_URL`) through `src/lib/api.ts`, never raw `fetch` scattered in components.
- API types live in `src/types/` and must match the backend's Pydantic schemas.
- Import local code via the `@/` alias.
- Every data view handles loading, empty and error states.
- Shared building blocks: `hooks/useLoader.ts` (data loading), `lib/dates.ts` (local dates; never use UTC for calendar dates), `components/ui/` (`Modal`, `ConfirmDialog`, `ApiImage` for backend-served images), button/input classes in `styles/globals.css`.
