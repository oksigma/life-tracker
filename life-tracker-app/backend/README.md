# Backend (Python, FastAPI, Uvicorn, MongoDB)

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12.

```bash
uv sync                                   # create .venv and install deps
uv run uvicorn app.main:app --reload      # http://localhost:8000  (docs at /docs)
uv run pytest                             # tests
uv run ruff check . && uv run ruff format .
```

- `app/main.py` — FastAPI app, CORS, router
- `app/core/config.py` — settings from `../.env`
- `app/db/mongo.py` — MongoDB client
- `app/api/router.py` — `/api` router; includes each module
- `app/modules/<area>/` — router → service → repository, with Pydantic schemas
- `tests/` — pytest
