# LifeTracker

## Project overview
An app that keeps a personal record of different parts of your life, a bit like a personal assistant:
clothing worn, health, movies seen, food eaten (with calories), drinks and exercise.
Product vision and goals: `docs/product/vision.md`. Roadmap: `docs/product/roadmap.md`.

## Current status
- **Phase:** 0 — Foundation (scaffold in place, no features built yet)
- **Active specs:** 0001 Movies, 0002 Clothing, 0003 Calendar, 0004 Food, 0005 Movie details, 0006 App password (all built; awaiting manual browser check; 0005 needs a TMDB key)
- **Deployment:** code on GitHub at `oksigma/life-tracker`; Vercel + Atlas setup in `docs/architecture/deployment.md`
- **Next up:** Health (weight, sleep, symptoms) and Exercise

## Tech stack
| Layer | Choice |
|---|---|
| Frontend | React + Next.js (App Router), TypeScript |
| Backend | Python 3.12, FastAPI, served by Uvicorn (managed with uv) |
| Database | MongoDB (local via Docker) |
| Testing | pytest (backend), e2e in `life-tracker-app/tests/e2e/` |
| Hosting | Vercel (frontend + backend) and MongoDB Atlas — ADR 0004 |

Full details in `life-tracker-app/CLAUDE.md`.

Changing anything in this table needs a decision record (`/new-adr`).

## Repository layout — important
- **This top-level folder is documentation only. Never put code here.**
- All code lives in `life-tracker-app/` (`frontend`, `backend`, `database`, `infra`). See `life-tracker-app/CLAUDE.md`.
- `docs/product/` — vision, feature areas, roadmap
- `docs/specs/` — feature specifications (one per feature)
- `docs/architecture/` — system overview and decision records in `decisions/`
- `docs/design/`, `docs/research/`, `docs/meeting-notes/`

## Common commands
Run from `life-tracker-app/`:
- `npm install` and `cd backend && uv sync` — install frontend and backend
- `npm run db:up` — start MongoDB
- `npm run dev` — frontend (:3000) and backend (:8000)
- `npm run lint` / `npm run test` / `npm run build`

## Workflow: spec first, then code
1. Every non-trivial feature starts as a spec in `docs/specs/` (use `/new-spec`, based on `docs/specs/_template.md`).
2. Have the `spec-reviewer` agent review the draft.
3. A spec moves `Draft` → `Approved` only when the user says so. Don't implement a `Draft` spec without asking.
4. Implement with `/implement-spec <spec file>`. Keep the spec's checklist and status up to date as you go.
5. If implementation needs to diverge from the spec, update the spec (and say why) rather than silently drifting.
6. Significant technical decisions (new library, data model change, auth approach) get a decision record via `/new-adr`.

## Definition of done
A feature is done when:
- [ ] All acceptance criteria in its spec pass
- [ ] Lint, type checks and tests pass for every changed workspace
- [ ] New behaviour has tests (pytest for backend routes and services, e2e for key flows)
- [ ] Spec status is `Done` and the spec index is updated
- [ ] `database/schema.md` and `docs/architecture/overview.md` reflect any changes

## Life areas
Clothing, health, movies, food, drinks. The frontend list is `life-tracker-app/frontend/src/types/life-area.ts`.
Each area has matching folders in `frontend/src/features/<area>`, `frontend/src/app/<area>` and
`backend/app/modules/<area>`. Use `/new-life-area` to add one.
Each area also needs registering on the calendar (spec 0003): backend `CalendarService`/`DayEntries` and frontend `features/calendar/areas.ts`.

## Privacy and security
This app stores personal data, including health information.
- Single-user app: no accounts. One app password (`APP_PASSWORD`, spec 0006) protects the deployed app.
- Never log personal entry content (health details, notes).
- Never commit secrets; config comes from `.env` (see `.env.example`).
- Don't add third-party analytics or integrations without a decision record.

## Do / Don't
- **Do** ask before adding a new dependency, and prefer well-maintained ones.
- **Do** keep changes small and focused on one spec.
- **Don't** put code in the top-level folder.
- **Don't** let frontend types drift from the backend's Pydantic schemas; the API's OpenAPI schema is the contract.
- **Don't** commit or push unless the user asks.

## Writing docs
- Markdown, plain language, short sections. Dates as `YYYY-MM-DD`.
- Meeting notes: `docs/meeting-notes/YYYY-MM-DD-topic.md`.
- Keep `docs/architecture/overview.md` and `life-tracker-app/database/schema.md` in sync with reality.

## Glossary
| Term | Meaning |
|---|---|
| Life area | A top-level category of tracking (e.g. movies, drinks) |
| Entry | A single logged record in a life area |
| Spec | A feature specification in `docs/specs/` |
| ADR | Architecture decision record in `docs/architecture/decisions/` |
