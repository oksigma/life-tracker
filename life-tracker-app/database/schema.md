# Collections (draft)

Single-user app: no `users` collection and no `user_id` fields.
Every document has `_id` (ObjectId), `created_at` and `updated_at` (UTC).

| Collection | Purpose | Example fields |
|---|---|---|
| `movies_seen` | Movies watched — see spec 0001 | title, year, watched_on, rating, notes |
| `outfits` | Outfit photos by day — see spec 0002 | worn_on, notes, photo_file_id, thumbnail_file_id |
| `health_entries` | Health records | date, type, value, notes — _TODO: define health types_ |
| `meals` | Meals — see spec 0004 | eaten_on, meal_type, items[], total_kcal, notes, photo_file_id, thumbnail_file_id |
| `foods` | "My foods": every food used, for reuse | key (unique), name, brand, kcal_per_100g, kcal_per_serving, use_count, last_used_at |
| `food_search_cache` | Cached Open Food Facts searches | query (unique), results, fetched_at (TTL 30 days) |
| `drink_entries` | Drinks | date, drink, quantity, unit, notes |

## File storage (GridFS)
- `outfit_photos` bucket (`outfit_photos.files`, `outfit_photos.chunks`): processed outfit JPEGs (full size and 400px thumbnail). Originals are never stored.
- `meal_photos` bucket: processed meal JPEGs (optional per meal).

## Indexes
- `movies_seen`: `{ watched_on: -1, created_at: -1 }` (list order), `{ title: 1 }`
- `outfits`: `{ worn_on: -1, created_at: -1 }`
- `meals`: `{ eaten_on: -1, created_at: -1 }`; `foods`: `key` unique, `{ use_count: -1, last_used_at: -1 }`; `food_search_cache`: `query` unique, TTL on `fetched_at`
- Other entry collections: `{ date: -1 }` (or the area's date field)
