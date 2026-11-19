from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.errors import NotFoundError
from app.db.indexes import ensure_indexes
from app.db.mongo import create_client
from app.modules.food.openfoodfacts import OpenFoodFactsClient, RateLimiter
from app.modules.movies.tmdb import TmdbClient


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    client = create_client()
    app.state.db = client[settings.mongodb_db]
    await ensure_indexes(app.state.db)
    http = httpx.AsyncClient(
        timeout=10.0, headers={"User-Agent": settings.food_database_user_agent}
    )
    app.state.food_database = OpenFoodFactsClient(
        http, RateLimiter(settings.food_database_searches_per_minute)
    )
    key = settings.tmdb_api_key.strip()
    app.state.tmdb = TmdbClient(http, key) if key else None
    yield
    await http.aclose()
    await client.close()


app = FastAPI(title="LifeTracker API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(NotFoundError)
async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


app.include_router(api_router)
