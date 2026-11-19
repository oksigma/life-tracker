# 0001. Movies — log movies I've seen

- **Status:** In progress
- **Area:** movies
- **Created:** 2026-11-14
- **Related:** `docs/product/features.md`, `life-tracker-app/database/schema.md`

## Summary
Keep a personal log of every movie I watch: what it was, when I watched it, where, and what I thought of it.
This is the first life area built, so it also sets the pattern (frontend feature + FastAPI module + MongoDB collection) for the others.

## User stories
- As me, I want to quickly log a movie I just watched so I don't forget it.
- As me, I want to see a list of everything I've watched, newest first.
- As me, I want to search my log by title so I can check whether I've seen something.
- As me, I want to edit or delete an entry if I got something wrong.
- As me, I want to log a rewatch so I can see how often I've watched a favourite.

## Requirements
### Must have
- Add a viewing with: **title** (required), **date watched** (required, defaults to today), **year of release** (optional),
  **rating** (optional, 1–5 stars), **where watched** (optional: cinema, home, streaming, other), **notes** (optional; labelled "Comments" in the UI and previewed in the list).
- Each viewing is its own entry; watching a movie again creates a new entry.
- List of all viewings, newest first, showing title, year, date watched, rating.
- Search the list by title (case-insensitive, partial match).
- View, edit and delete a single entry. Deleting asks for confirmation.
- Validation: title 1–200 characters; date not in the future; year between 1888 and next year; rating 1–5.

### Nice to have
- Filter the list by rating or by year watched.
- Show "watched N times" next to titles seen more than once.
- Simple stats at the top: total movies this year, average rating.

### Out of scope
- Looking up movie details or posters from an external service (e.g. TMDB). Possible later spec.
- Watchlist ("want to see").
- Sharing or social features.

## UX
- **`/movies`** — page title, "Log a movie" button, search box, list of viewings.
  - Empty state: "No movies logged yet", with the "Log a movie" button.
  - Loading state: skeleton rows. Error state: message with a retry button.
- **Log / edit form** — a modal or `/movies/new` and `/movies/[id]/edit` pages. Title field focused on open; date defaults to today; star picker for rating.
- **`/movies/[id]`** — entry detail with edit and delete actions.
- Mobile-friendly: single column on small screens. Styled with Tailwind.

## Data model
Collection `movies_seen`:

| Field | Type | Notes |
|---|---|---|
| `_id` | ObjectId | Exposed as `id: string` in the API |
| `title` | string | Required, trimmed, 1–200 chars |
| `year` | int \| null | Release year |
| `watched_on` | date (stored as `YYYY-MM-DD` string) | Required; a calendar date, not a timestamp |
| `rating` | int \| null | 1–5 |
| `where` | `"cinema"` \| `"home"` \| `"streaming"` \| `"other"` \| null | |
| `notes` | string \| null | Up to 2000 chars |
| `created_at` / `updated_at` | datetime (UTC) | Set by the backend |

Indexes: `{ watched_on: -1 }`; `{ title: 1 }` for search.

## API
All under `/api/movies`. Bodies are JSON; validation errors return `422` (FastAPI default).

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/movies?q=&limit=&offset=` | `q` searches title | `200` `{ items: Movie[], total: number }` |
| POST | `/api/movies` | `MovieCreate` | `201` `Movie` |
| GET | `/api/movies/{id}` | — | `200` `Movie`, `404` if missing |
| PATCH | `/api/movies/{id}` | `MovieUpdate` (any subset of fields) | `200` `Movie`, `404` if missing |
| DELETE | `/api/movies/{id}` | — | `204`, `404` if missing |

`Movie` = all fields above with `id` instead of `_id`. Invalid ids return `404`.

## Acceptance criteria
- [ ] Given no entries, when I open `/movies`, then I see the empty state. _(needs a manual check in the browser)_
- [ ] Given I submit the form with a title only, then an entry is created with today's date and appears at the top of the list. _(needs a manual check in the browser)_
- [ ] Given I enter a future date, a rating of 6, or an empty title, then the form shows an error and nothing is saved (and the API rejects it with `422`). _(API side verified by tests; form needs a manual check)_
- [x] Given entries exist, when I search "matrix", then only entries whose title contains "matrix" (any case) are shown.
- [ ] Given an entry, when I edit its rating and save, then the list shows the new rating. _(needs a manual check in the browser)_
- [ ] Given an entry, when I delete it and confirm, then it disappears from the list; cancelling leaves it. _(needs a manual check in the browser)_
- [x] Given I log the same title twice, then both viewings appear as separate entries.
- [x] Data survives restarting the backend (stored in MongoDB).

## Implementation checklist
- [x] Backend Pydantic schemas (`MovieCreate`, `MovieUpdate`, `Movie`, list response)
- [x] MongoDB collection and indexes (update `database/schema.md`)
- [x] Backend module (router, service, repository) + pytest tests — 32 tests
- [x] Frontend types matching the API
- [x] Frontend feature + pages (list, form, detail)
- [ ] End-to-end test — deferred (see Decisions)
- [x] Docs updated

## Implementation notes
- `watched_on` is a calendar date; the API accepts dates up to "today" in the furthest-ahead time zone (UTC+14) so no user's today is rejected.
- Timestamps are rounded to milliseconds to match MongoDB's precision.
- Search escapes regex characters, so it is always a plain text match.
- Nice-to-haves (filters, rewatch counts, stats) not built yet.

## Decisions (resolved open questions)
- **Rating:** 1–5 whole stars.
- **Form:** pop-up modal over the list for add and edit.
- **Delete:** permanent (hard delete), with a confirmation step.
- **E2E testing:** deferred; no Playwright yet. Acceptance criteria are covered by backend tests and manual checks for now.
- 2026-11-15: the notes field is labelled "Comments" in the UI, and the first two lines show under each movie in the list. The API field stays `notes`.
