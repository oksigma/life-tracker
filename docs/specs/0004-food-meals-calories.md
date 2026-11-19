# 0004. Food — log meals with a photo and estimated calories

- **Status:** In progress (approved by request, 2026-11-14)
- **Area:** food
- **Created:** 2026-11-14
- **Related:** `0002-clothing-outfit-photos.md` (photo handling), `0003-calendar.md`

## Summary
Log what I ate: an optional photo of the meal, which meal it was, and the foods in it. Calories are **estimated**
by looking each food up in [Open Food Facts](https://world.openfoodfacts.org) (a free, open food database) and
scaling by the amount I enter, or by typing calories in myself. No AI; the photo is for my own record.

## User stories
- As me, I want to snap my meal, add "toast 2 slices" and "banana", and see roughly how many calories that was.
- As me, I want foods I've used before to come up instantly, without searching the database again.
- As me, I want to see my calorie total for each day.
- As me, I want to enter calories by hand when a food isn't in the database.

## Requirements
### Must have
- A meal has: **date eaten** (defaults to today), **meal type** (breakfast / lunch / dinner / snack), optional **photo**,
  optional **notes**, and a list of **food items**.
- Food item: name, amount (quantity + unit: grams, ml or servings), and calories.
  - From the database: calories = kcal per 100 g × grams ÷ 100, or kcal per serving × servings. The backend recomputes this, so totals are always consistent.
  - Manual: I type the calories (amount optional).
- **Food search:**
  - "My foods" — foods I've used before — are searched instantly as I type (local, no limits).
  - The Open Food Facts search runs only when I press "Search food database" (their limit is 10 searches/minute; no search-as-you-type).
  - Database results without calorie data are hidden. Results are cached for 30 days.
  - Every food used in a saved meal is remembered in "My foods".
- Meal total and **daily total** calories, shown as estimates ("≈ 650 kcal").
- List of meals grouped by day (newest first) with each day's total; meal detail page; edit (date, type, notes, items); delete with confirmation (removes the photo too).
- Photos use the same processing as clothing: JPEG/PNG/WebP/HEIC up to 15 MB, rotated upright, resized, **all metadata (incl. GPS) stripped**.
- Food appears on the calendar as 🍽️ (amber); the day panel lists meals with their calories.
- If the food database is unreachable or rate-limited, show a clear message; manual entry and "My foods" still work.

### Nice to have
- Barcode scanning for packaged foods.
- Daily calorie target and progress.
- Add or replace a photo after the meal is saved.

### Out of scope
- AI recognition of food from photos.
- Macronutrients (protein, fat, carbs) — the data is there, so this could be a later spec.
- Drinks (separate area).

## Data model
**`meals`**

| Field | Type | Notes |
|---|---|---|
| `eaten_on` | `YYYY-MM-DD` | |
| `meal_type` | `breakfast` \| `lunch` \| `dinner` \| `snack` | |
| `notes` | string \| null | ≤ 1000 chars |
| `items` | `MealItem[]` | ≤ 50 |
| `total_kcal` | number | Sum of item kcal, computed by backend |
| `photo_file_id`, `thumbnail_file_id` | ObjectId \| null | GridFS bucket `meal_photos` |
| `created_at`, `updated_at` | datetime | |

**`MealItem`**: `name` (1–200), `quantity` (> 0) \| null, `unit` (`g` \| `ml` \| `serving`) \| null,
`kcal_per_100g` \| null, `kcal_per_serving` \| null, `kcal` (0–10 000), `source` (`openfoodfacts` \| `manual`), `off_code` \| null.

**`foods`** ("My foods"): name, brand, kcal_per_100g, kcal_per_serving, serving_size, source, off_code, use_count, last_used_at.
Unique by `off_code`, or by lower-cased name + brand for manual foods.

**`food_search_cache`**: query, results, fetched_at (TTL index: 30 days).

## API (all under `/api/food`)
| Method | Path | Notes |
|---|---|---|
| GET | `/meals?limit=&offset=` | `{ items: Meal[], total }`, newest first |
| POST | `/meals` | multipart: `photo` (optional), `eaten_on`, `meal_type`, `notes`, `items` (JSON string) → `201 Meal` |
| GET / PATCH / DELETE | `/meals/{id}` | PATCH is JSON `{ eaten_on?, meal_type?, notes?, items? }` |
| GET | `/meals/{id}/photo`, `/meals/{id}/thumbnail` | JPEG; `404` if the meal has no photo |
| GET | `/foods?q=` | Search "My foods" (most used first) |
| GET | `/lookup?q=` | Search Open Food Facts → `{ results: FoodOption[] }`; `429` when rate-limited, `502` if unreachable |

## Open Food Facts usage
- Search via `https://search.openfoodfacts.org/search?q=…`, falling back to the legacy `https://world.openfoodfacts.org/cgi/search.pl`.
- Custom `User-Agent: LifeTracker/0.1 (personal app)`. Only the search words are sent — no photos or personal data.
- Backend enforces ≤ 10 searches/minute and caches results, so the app never gets blocked.
- Data licence: ODbL — fine for personal use; credit "Data from Open Food Facts" in the UI.

## Acceptance criteria
- [x] Given I log lunch with no photo and "banana 120 g" (89 kcal/100 g), then the meal total is ≈ 107 kcal. _(API verified; UI needs a manual check)_
- [x] Given I add a manual item "homemade soup, 250 kcal", then it counts towards the total. _(API verified; UI needs a manual check)_
- [ ] Given I used "banana" before, when I type "ban", then it appears under My foods without a database search. _(backend verified; needs a manual check in the browser)_
- [ ] Given two meals on a day, then the day header shows their combined total. _(backend verified; needs a manual check in the browser)_
- [x] Given I upload a photo, then it is stored without metadata and shown on the meal. _(API verified; UI needs a manual check)_
- [ ] Given the database is rate-limited or offline, then I see a message and can still enter calories manually. _(backend verified; needs a manual check in the browser)_
- [ ] Given I edit an item's quantity, then its calories and the totals update. _(backend verified; needs a manual check in the browser)_
- [x] Given a meal, it appears on the calendar as 🍽️ on its day; deleting it removes it and its photo. _(API verified; UI needs a manual check)_

## Implementation checklist
- [x] Move photo processing to `app/core/images.py` (shared by clothing and food)
- [x] Open Food Facts client (search, fallback, rate limit, cache) — mocked in tests
- [x] Food backend module (meals, my foods, lookup) + pytest tests — 48 tests
- [x] Register food on the calendar (backend + frontend)
- [x] Shared photo picker component (clothing + food)
- [x] Frontend: meals list with daily totals, meal form with food search, detail page
- [x] Docs updated

## Implementation notes
- Live check against Open Food Facts: "banana" → 20 results with calories (e.g. Banana 89 kcal/100g, Bananas USDA 88.9); second search served from cache.
- Meal type defaults from the time of day (breakfast before 11:00, lunch until 15:00, dinner 17:00–22:00, otherwise snack).
- Manual foods are remembered with a derived basis: per 100 g/ml if an amount in g/ml was given, otherwise per serving.
- A new meal needs a photo or at least one food.
