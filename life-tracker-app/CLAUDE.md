# LifeTracker — app code

<!--
HOW TO FILL THIS IN
- Replace each _TODO_ line with your decision. Short bullet points are best.
- Lines without _TODO_ are decided; change them if you disagree.
-->

## Overview
A personal record of different aspects of someone's life, a bit like a personal assistant.
Specs for features live in `../docs/specs/`; read the relevant spec before building a feature.

Life areas tracked:
- **Clothing** — clothes that are worn
- **Health** — weight, sleep, symptoms / how I feel (optional photo)
- **Movies** — movies seen
- **Food** — meals with optional photo and estimated calories
- **Drinks** — what you have had to drink
- **Exercise** — workouts (separate area)

- **Single user:** the app is just for me. No accounts or multi-user features.
- _TODO: Platforms: web only, or mobile-friendly web / native app later?_

## Tech stack and key libraries
| Concern | Choice |
|---|---|
| Frontend framework | React 19 + Next.js 16 (App Router), TypeScript |
| Styling | Tailwind CSS v4 (utility classes; no separate CSS files except `globals.css`) |
| UI component library | _TODO: e.g. shadcn/ui, MUI, none_ |
| Data fetching / client state | _TODO: e.g. TanStack Query, Server Components_ |
| Forms | _TODO: e.g. React Hook Form_ |
| Backend | Python 3.12, FastAPI, served by Uvicorn |
| Python package manager | uv |
| Validation (backend) | Pydantic |
| Database | MongoDB (local: Docker container) |
| MongoDB driver | PyMongo async (`AsyncMongoClient`) |
| File / photo storage | MongoDB GridFS (`AsyncGridFSBucket`) |
| Movie details | TMDB API (`TMDB_API_KEY` in `.env`; optional — off when empty) |
| Food calorie data | Open Food Facts (search-a-licious, legacy search fallback) via httpx; no AI |
| Image processing | Pillow + pillow-heif (HEIC); all uploads re-encoded as JPEG with metadata stripped |
| Authentication | Single app password (`APP_PASSWORD`, spec 0006): signed HttpOnly cookie, 90 days; off when empty |
| Hosting | Vercel (frontend + FastAPI as Python function) and MongoDB Atlas (ADR 0004) |
| Backend tests | pytest |
| Frontend tests | _TODO: e.g. Vitest + React Testing Library_ |
| End-to-end tests | _TODO: e.g. Playwright_ |
| Lint / format | Ruff (Python); ESLint with `eslint-config-next` (frontend); _TODO: Prettier?_ |

## Workspaces
- `frontend/` — Next.js web app. See `frontend/CLAUDE.md`.
- `backend/` — FastAPI app under `/api`. See `backend/CLAUDE.md`.
- `database/` — collection/index docs (`schema.md`) and seed data.
- `infra/` — docker-compose (local MongoDB), Dockerfiles, CI.
- `tests/e2e/` — end-to-end tests.

## Getting started
- Node.js _TODO: version (e.g. 20 LTS)_, Python 3.12, [uv](https://docs.astral.sh/uv/), Docker Desktop
- `cp .env.example .env`; optionally add a free TMDB key (`TMDB_API_KEY`) for movie posters and details
- `npm install` (frontend) and `cd backend && uv sync` (backend)

## Commands (run from this folder)
- `npm run db:up` / `npm run db:down` — start / stop MongoDB (host port **27018**, not the default 27017)
- `npm run dev` — frontend (:3000) + backend (:8000, API docs at http://localhost:8000/docs)
- `npm run dev:frontend` / `npm run dev:backend` — one side only
- `npm run lint` / `npm run test` / `npm run build`
- Backend directly: `cd backend && uv run uvicorn app.main:app --reload`, `uv run pytest`, `uv run ruff check .`
- _TODO: seed command_

## Architecture and data flow
- Browser → Next.js frontend → FastAPI (`/api`) → MongoDB.
- The backend's OpenAPI schema (`/openapi.json`) is the contract between frontend and backend.
  _TODO: generate frontend TypeScript types from it (e.g. `openapi-typescript`), or write them by hand?_
- _TODO: Any background jobs (e.g. reminders)? How should they run?_

## Data model and database
- MongoDB `_id` (ObjectId), exposed to the API as a string `id`.
- Collection and field names: `snake_case`, plural collections (e.g. `movies_seen`).
- Every document has `created_at` and `updated_at` (UTC). No `user_id`: single user.
- Dates stored as UTC; convert to the user's time zone only in the UI.
- _TODO: Soft delete (`deleted_at`) or hard delete?_
- _TODO: How "a day" is defined for daily tracking (user's local midnight?)_

## API conventions
- REST, plural resources: e.g. `/api/movies`, `/api/movies/{id}`, `/api/clothing/items`.
- Request/response bodies defined as Pydantic models in each module's `schemas.py`.
- _TODO: Response shape (plain objects, or `{ data }` / `{ error }` envelope?)_
- _TODO: Pagination style (page/limit or cursor)_
- _TODO: Versioning (`/api/v1`?)_

## Authentication and authorization
- Single user, so no accounts, roles or per-user data scoping.
- One app password (spec 0006). With `APP_PASSWORD` empty (local) there is no login; when set, every `/api` route except `/api/health` and `/api/auth/*` needs the session cookie. **Always set it when deployed.**

## Frontend conventions
- Organize by life area: `src/features/<area>/`; pages in `src/app/` stay thin.
- _TODO: Design reference (link to `../docs/design/`, colours, fonts)_
- _TODO: Light/dark mode? Mobile-first?_

## Backend conventions
- Each module in `app/modules/<area>/`: `router.py` → `service.py` → `repository.py`, models in `schemas.py`.
- Use `async def` for routes and database calls.
- Type hints everywhere; Ruff must pass.

## Code style
- TypeScript strict on the frontend; no `any` without a comment explaining why.
- Python: PEP 8 via Ruff, line length 100.
- _TODO: Named or default exports (frontend)? Comment style?_

## Testing
- Backend: pytest; every route has at least one test.
- _TODO: Frontend testing expectations_
- _TODO: Test database approach (separate MongoDB database, mongomock, test containers)_

## Error handling and logging
- _TODO: How errors are shown to users (toasts, inline messages)_
- Never log personal entry content (health details, notes).

## Security and privacy
- This app holds personal data, including health information and photos.
- Uploaded photos: strip all EXIF/metadata (especially GPS) and never keep the original file.
- External services: TMDB (movie titles/years only) and Open Food Facts: send search words only, with `User-Agent: LifeTracker/0.1 (personal app)` — never photos or personal data. Respect its 10 searches/minute limit (enforced and cached in the backend).
- Never commit secrets. Config comes from `.env` (see `.env.example`).
- _TODO: Data export and account deletion requirements_

## Git workflow
- _TODO: Branch naming, commit message style, PRs or straight to `main`_

## Deployment and environments
- Vercel + MongoDB Atlas (ADR 0004). Step-by-step setup: `../docs/architecture/deployment.md`.
- Two Vercel projects from `oksigma/life-tracker`: frontend (root `life-tracker-app/frontend`) and backend (root `life-tracker-app/backend`, entrypoint in `pyproject.toml`). The frontend proxies `/api/*` to `BACKEND_URL`.
- Vercel limits request bodies to 4.5 MB, so the browser shrinks larger photos before upload (`lib/photos.ts`).

## Known issues and gotchas
- _TODO: Add as you find them_

## Claude: always / never
- Always read the relevant spec in `../docs/specs/` before building a feature.
- Always run lint and tests for changed parts before saying work is done.
- _TODO: Anything else Claude must always / never do_
