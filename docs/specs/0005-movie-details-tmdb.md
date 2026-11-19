# 0005. Movies — add details from TMDB

- **Status:** In progress (approved by request, 2026-11-14)
- **Area:** movies
- **Created:** 2026-11-14
- **Related:** `0001-movies.md` (this was listed there as a possible later spec)

## Summary
When I log a movie, the app finds it on [TMDB](https://www.themoviedb.org) (The Movie Database) and adds its
**poster, plot summary, runtime, genres and release year**. Longer information is collapsible so it doesn't take up space.

## User stories
- As me, I want to type a title and pick the right movie from suggestions (with posters), so details are correct.
- As me, I want details added automatically even if I don't pick a suggestion.
- As me, I want to fix a wrong match, or add details to movies I logged before.

## Requirements
### Must have
- **Suggestions while typing the title** (from 2 characters, debounced): poster thumbnail, title, year. Picking one sets the title and year and links the movie to TMDB.
- **Automatic match on save** if no suggestion was picked: exact title (and year, if given) wins, else the top result. A TMDB failure never blocks saving the movie.
- Stored details: TMDB id, poster, plot summary, runtime, genres, release date/year, original title. The year field is filled from TMDB if left empty.
- **List:** small poster next to each movie; runtime and genres on a second line.
- **Movie page:** poster, year · runtime · genres; **plot summary and "More info" in collapsible sections** (closed by default).
- **Change match** ("Wrong movie?") — search TMDB and pick another; **Find details** for movies without any; **Remove details**.
- Without a TMDB key the app works as before, and the form explains how to turn details on.
- TMDB attribution on movie pages (required by TMDB's terms).

### Out of scope
- Director and cast (could be added later; TMDB has them).
- Watchlist, recommendations, ratings from other sites.

## API (under `/api/movies`)
| Method | Path | Notes |
|---|---|---|
| GET | `/tmdb/status` | `{ configured: bool }` |
| GET | `/tmdb/search?q=&year=` | `{ results: TmdbMatch[] }` — `503` if no key, `502` if TMDB fails |
| POST | `/movies` | Accepts optional `tmdb_id`; details attached automatically |
| POST | `/{id}/details` | Body `{ tmdb_id? }`: match to that movie, or auto-match by title; returns `Movie` |
| DELETE | `/{id}/details` | Remove details; returns `Movie` |

`Movie.details`: `{ tmdb_id, title, original_title, release_date, year, runtime, genres[], overview, poster_path }` or `null`.

## Setup
Create a free TMDB account → Settings → API → request an API key, then add to `life-tracker-app/.env`:
`TMDB_API_KEY=<your API key or API Read Access Token>` and restart the backend.

## Privacy
Only movie titles (and years) are sent to TMDB. Posters load in the browser from `image.tmdb.org`.

## Acceptance criteria
- [ ] Typing "dune" shows suggestions with posters; picking "Dune (2021)" saves it with poster, plot, runtime, genres. _(needs a TMDB key and a manual check)_
- [ ] Saving "Arrival" without picking a suggestion still attaches the right details. _(needs a TMDB key and a manual check)_
- [x] If TMDB is down or no key is set, the movie still saves (without details). _(tests)_
- [ ] "Wrong movie?" lets me pick a different match; "Remove details" clears them. _(needs a TMDB key and a manual check)_
- [ ] Plot and More info are collapsed by default and expand on tap. _(needs a TMDB key and a manual check)_
- [ ] Movies logged before this feature can get details via "Find details". _(needs a TMDB key and a manual check)_

## Implementation checklist
- [x] TMDB client (search, details, key or read-token auth) — mocked in tests
- [x] Movie schemas, service and routes + pytest tests — 26 tests (TMDB faked; no live calls)
- [x] Frontend: title suggestions, list posters, detail page with collapsible sections, change match
- [x] `.env.example`, docs

## Implementation notes
- Not yet tested against the live TMDB API: no key was available while building. All behaviour is covered with a fake TMDB and mocked HTTP.
- `.env` is not edited by Claude (secrets file); add `TMDB_API_KEY=...` there yourself. Tests force the key off so they never call TMDB.
- On phones, Edit/Delete buttons are hidden from the movie list rows (they're on each movie's page) to keep rows uncluttered.
