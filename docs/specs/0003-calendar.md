# 0003. Calendar — see which days I logged things

- **Status:** In progress (approved by request, 2026-11-14)
- **Area:** cross-cutting
- **Created:** 2026-11-14
- **Related:** `0001-movies.md`, `0002-clothing-outfit-photos.md`

## Summary
A month calendar showing, for every day, a symbol for each kind of thing I logged (🎬 movie, 👕 outfit, …).
Clicking a day shows what was logged. It works across all life areas, so new areas appear on it automatically
once they are registered.

## User stories
- As me, I want to see at a glance which days I logged something, and what kind of thing.
- As me, I want to move between months.
- As me, I want to click a day and see the movies and outfits from that day, and open them.

## Requirements
### Must have
- Month grid, weeks starting Monday, with previous / next month and a "Today" button.
- Each day shows one symbol per life area with entries that day; a count when there is more than one (e.g. `🎬2`).
- Symbols are distinct icons **and** colours (not colour alone), with a legend.
- Today is highlighted; days outside the current month and future days are dimmed.
- Click a day → a panel lists that day's entries per area (movie title + rating; outfit thumbnails), each linking to its page.
- Month and selected day are kept in the URL (`/calendar?month=2026-11&day=2026-11-14`) so the back button and links work.
- Link to the calendar from the home page.

### Nice to have
- "Log a movie / outfit for this day" buttons in the day panel, pre-filling the date.
- Year view / heatmap.

### Out of scope
- Editing entries from the calendar (use the area's own page).

## Symbols
| Area | Symbol | Colour |
|---|---|---|
| Movies | 🎬 | violet |
| Clothing | 👕 | sky |
| Health (later) | ❤️ | rose |
| Food (later) | 🍽️ | amber |
| Drinks (later) | 🥤 | emerald |

## API
| Method | Path | Response |
|---|---|---|
| GET | `/api/calendar?start=YYYY-MM-DD&end=YYYY-MM-DD` | `200` `{ start, end, days: [{ date, counts: { movies?: n, clothing?: n } }] }` — only days with entries; range ≤ 366 days, `end ≥ start`, else `422` |
| GET | `/api/calendar/days/{date}` | `200` `{ date, movies: Movie[], clothing: Outfit[] }` |

Each life area contributes through its repository (`count_by_day`, `list_on_day`), so the calendar module doesn't
query other areas' collections directly.

## Acceptance criteria
- [ ] Given a movie and two outfits logged on 10 Nov, when I view November, then 10 Nov shows 🎬 and 👕2. _(needs a manual check in the browser)_
- [ ] Given no entries in a month, then the calendar shows no symbols (and a short "nothing logged this month" note). _(needs a manual check in the browser)_
- [ ] When I click 10 Nov, then I see the movie and both outfit thumbnails, each linking to its page. _(needs a manual check in the browser)_
- [ ] When I press next / previous / Today, then the month changes and the URL updates; reloading keeps the same view. _(needs a manual check in the browser)_
- [x] Given I change an outfit's date, then the calendar reflects the new day. _(API verified)_
- [x] The API rejects an invalid date, `end` before `start`, or a range over 366 days with `422`.

## Implementation checklist
- [x] `count_by_day` / `list_on_day` on the movies and clothing repositories
- [x] Calendar backend module (router, service, schemas) + pytest tests — 14 tests
- [x] Frontend: area symbol config, month grid, legend, day panel, URL state
- [x] Home page link
- [x] Docs updated

## Implementation notes
- Day cells show icon + colour chips with a count when > 1; each cell has a full screen-reader label (e.g. "Tuesday 10 November 2026: 1 movie, 2 outfits").
- Month data is fetched for the whole visible grid (including neighbouring-month days); the day panel only calls the API for days that have entries.
- Areas are registered in `frontend/src/features/calendar/areas.ts` and the backend `CalendarService`.
