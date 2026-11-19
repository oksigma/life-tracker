# 0002. Clothing — log what I'm wearing with a photo

- **Status:** In progress (approved by request, 2026-11-14)
- **Area:** clothing
- **Created:** 2026-11-14
- **Related:** `0001-movies.md` (same patterns), `life-tracker-app/database/schema.md`

## Summary
Upload a photo of what I'm wearing and log the day I wore it. The date defaults to the day of upload and can be changed,
so I can catch up on past days. Over time this builds a visual diary of my outfits.

## User stories
- As me, I want to take or pick a photo of my outfit and log it in a few taps.
- As me, I want the date to default to today, but be able to change it when I'm logging an earlier day.
- As me, I want to scroll back through my outfits by date.
- As me, I want to fix the date of an entry, or delete it, if I got it wrong.

## Requirements
### Must have
- Log an outfit with: **photo** (required), **date worn** (required; defaults to the upload date, i.e. today in my time zone), **notes** (optional, up to 1000 chars).
- Change the date (and notes) on an existing entry.
- Gallery of outfits, newest date first, grouped by date.
- View a single outfit large; edit date/notes; delete (with confirmation). Deleting removes the photo too.
- More than one outfit per day is allowed (e.g. a change for the evening).
- Photo rules:
  - Accepts JPEG, PNG, WebP and HEIC/HEIF (iPhone photos), up to 15 MB.
  - Stored as JPEG, resized to at most 2000 px on the long side, plus a 400 px thumbnail for the gallery.
  - Rotated upright using the camera's orientation data.
  - **All metadata (EXIF) is stripped**, including GPS location, so photos never carry where they were taken.
- Date can't be in the future.

### Nice to have
- Pre-fill the date from the photo's "date taken" when it differs from today.
- Calendar view.
- Replace the photo on an existing entry.

### Out of scope
- Tagging individual clothing items / building a wardrobe (possible later spec).
- Multiple photos per entry.
- Cloud photo storage.

## UX
- **`/clothing`** — title, "Log an outfit" button, gallery grid of thumbnails grouped under date headings (e.g. "Sat 14 Nov 2026").
  - Empty state: "No outfits logged yet", with the button. Loading skeleton; error state with retry.
- **Log form (modal)** — choose/take a photo (on phones this offers the camera), preview of the chosen photo,
  date field defaulting to today, notes, Save. Shows upload progress state ("Uploading…") and errors (wrong file type, too large).
- **`/clothing/[id]`** — large photo, date, notes, Edit (date + notes) and Delete.
- Mobile-first: 2-column grid on phones, 3–4 on larger screens.

## Data model
Collection `outfits`:

| Field | Type | Notes |
|---|---|---|
| `_id` | ObjectId | Exposed as `id: string` |
| `worn_on` | `YYYY-MM-DD` string | Calendar date |
| `notes` | string \| null | Up to 1000 chars |
| `photo_file_id` | ObjectId | GridFS file: full-size JPEG |
| `thumbnail_file_id` | ObjectId | GridFS file: 400 px JPEG |
| `created_at` / `updated_at` | datetime (UTC) | Set by backend |

Photos are stored in MongoDB GridFS bucket `outfit_photos` (so backing up the database backs up the photos).
Indexes: `{ worn_on: -1, created_at: -1 }`.

## API
All under `/api/clothing`.

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/outfits?limit=&offset=` | — | `200` `{ items: Outfit[], total }`, newest first |
| POST | `/outfits` | `multipart/form-data`: `photo` (file), `worn_on` (date, optional → today), `notes` (optional) | `201` `Outfit` |
| GET | `/outfits/{id}` | — | `200` `Outfit`, `404` |
| PATCH | `/outfits/{id}` | JSON `{ worn_on?, notes? }` | `200` `Outfit`, `404` |
| DELETE | `/outfits/{id}` | — | `204` (also deletes photos), `404` |
| GET | `/outfits/{id}/photo` | — | `200` JPEG, `404` |
| GET | `/outfits/{id}/thumbnail` | — | `200` JPEG, `404` |

`Outfit` = `{ id, worn_on, notes, photo_url, thumbnail_url, created_at, updated_at }` (URLs are API paths).
Errors: not an image / unsupported type → `415`; over 15 MB → `413`; bad fields → `422`.

## Acceptance criteria
- [ ] Given no outfits, when I open `/clothing`, then I see the empty state. _(needs a manual check in the browser)_
- [ ] Given I choose a photo and save without touching the date, then an outfit is logged for today and appears at the top of the gallery. _(needs a manual check in the browser)_
- [ ] Given I change the date to last Tuesday before saving, then the outfit appears under last Tuesday. _(needs a manual check in the browser)_
- [ ] Given an existing outfit, when I change its date, then it moves to the new date in the gallery. _(needs a manual check in the browser)_
- [x] Given a photo with GPS data, when it is uploaded, then the stored photo and thumbnail contain no EXIF metadata.
- [x] Given a photo taken sideways (EXIF orientation), then it is stored upright.
- [x] Given a HEIC photo from an iPhone, then it uploads and displays in any browser. _(backend verified; please try a real iPhone photo)_
- [x] Given a PDF or a 20 MB file, then upload is rejected with a clear message and nothing is saved.
- [x] Given a future date, then the form and API reject it. _(API verified; form needs a manual check)_
- [x] Given I delete an outfit and confirm, then it disappears and its photos are removed from storage. _(API verified; UI needs a manual check)_

## Implementation checklist
- [x] Backend deps: `python-multipart` (uploads), `Pillow` + `pillow-heif` (image processing)
- [x] Image processing (validate, orient, strip metadata, resize, thumbnail)
- [x] Backend Pydantic schemas
- [x] MongoDB collection, GridFS bucket, indexes (update `database/schema.md`)
- [x] Backend module (router, service, repository) + pytest tests — 29 tests
- [x] Frontend types matching the API
- [x] Frontend feature + pages (gallery, log form, detail)
- [x] Docs updated

## Implementation notes
- Gallery loads the latest 200 outfits; a "load more" control is needed once there are more.
- HEIC previews don't display in Chrome/Firefox before upload (the form says so); after upload they are JPEGs and display everywhere.
- Photos are served with long-lived cache headers since an outfit's photo never changes.

## Decisions
- **Photo storage:** MongoDB GridFS — no extra services, and photos are backed up with the database.
- **Privacy:** strip all EXIF on upload; keep only the processed JPEGs, never the original file.
- **Default date** is set by the browser (my local "today"); the API falls back to the server's date if none is sent.
