# Backend (Python, FastAPI, Uvicorn, MongoDB)

- Run with `uv run uvicorn app.main:app --reload` (port 8000; interactive docs at `/docs`).
- Manage dependencies with uv only: `uv add <pkg>`, `uv add --dev <pkg>`. Don't use pip or edit `uv.lock` by hand.
- App entry: `app/main.py`. All routes under `/api`, included in `app/api/router.py`.
- Settings in `app/core/config.py` (pydantic-settings, reads `../.env`). Don't read `os.environ` directly.
- MongoDB client in `app/db/mongo.py` (PyMongo `AsyncMongoClient`). Only repositories touch the database.
- Each module in `app/modules/<area>/`:
  - `router.py` — FastAPI routes, HTTP concerns only
  - `schemas.py` — Pydantic request/response models (convert `_id` ObjectId → `id: str`)
  - `service.py` — business logic
  - `repository.py` — MongoDB queries
- Shared helpers in `app/core/`: `time.py` (`utc_now`, `validate_not_future`), `ids.py` (`parse_object_id`), `errors.py` (`NotFoundError` → 404).
- Use `async def` throughout; type hints everywhere. CPU-heavy work (e.g. image processing) goes in `asyncio.to_thread`.
- Raise `HTTPException` (or custom exceptions handled centrally) — never return raw error details or stack traces.
- Tests in `tests/` with pytest and FastAPI `TestClient`. Run `uv run pytest` and `uv run ruff check .` before finishing.
