from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pymongo.asynchronous.database import AsyncDatabase

from app.core.errors import NotFoundError
from app.db.mongo import get_db
from app.modules.movies.repository import MovieRepository
from app.modules.movies.schemas import (
    AttachDetails,
    Movie,
    MovieCreate,
    MovieList,
    MovieUpdate,
    TmdbSearchResults,
    TmdbStatus,
)
from app.modules.movies.service import MovieService
from app.modules.movies.tmdb import (
    TmdbClient,
    TmdbError,
    TmdbNotConfiguredError,
    TmdbNotFoundError,
    get_tmdb,
)

router = APIRouter(prefix="/movies", tags=["movies"])


def get_service(
    db: Annotated[AsyncDatabase, Depends(get_db)],
    tmdb: Annotated[TmdbClient | None, Depends(get_tmdb)],
) -> MovieService:
    return MovieService(MovieRepository(db), tmdb)


ServiceDep = Annotated[MovieService, Depends(get_service)]


@contextmanager
def tmdb_errors() -> Iterator[None]:
    """Turn TMDB problems into clear HTTP errors."""
    try:
        yield
    except TmdbNotConfiguredError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Movie details are off: add TMDB_API_KEY to the .env file and restart the backend.",
        ) from None
    except TmdbNotFoundError:
        raise NotFoundError("Movie on TMDB") from None
    except TmdbError:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Couldn't reach TMDB. Try again in a moment."
        ) from None


@router.get("")
async def list_movies(
    service: ServiceDep,
    q: Annotated[str | None, Query(max_length=200, description="Search titles")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MovieList:
    return await service.list(q, limit, offset)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_movie(service: ServiceDep, payload: MovieCreate) -> Movie:
    return await service.create(payload)


@router.get("/tmdb/status")
async def tmdb_status(tmdb: Annotated[TmdbClient | None, Depends(get_tmdb)]) -> TmdbStatus:
    return TmdbStatus(configured=tmdb is not None)


@router.get("/tmdb/search")
async def search_tmdb(
    service: ServiceDep,
    q: Annotated[str, Query(min_length=2, max_length=200)],
    year: Annotated[int | None, Query(ge=1888, le=2100)] = None,
) -> TmdbSearchResults:
    with tmdb_errors():
        return TmdbSearchResults(results=await service.search_tmdb(q, year))


@router.get("/{movie_id}")
async def get_movie(service: ServiceDep, movie_id: str) -> Movie:
    return await service.get(movie_id)


@router.patch("/{movie_id}")
async def update_movie(service: ServiceDep, movie_id: str, payload: MovieUpdate) -> Movie:
    return await service.update(movie_id, payload)


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(service: ServiceDep, movie_id: str) -> Response:
    await service.delete(movie_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{movie_id}/details")
async def attach_details(service: ServiceDep, movie_id: str, payload: AttachDetails) -> Movie:
    with tmdb_errors():
        return await service.attach_details(movie_id, payload.tmdb_id)


@router.delete("/{movie_id}/details")
async def remove_details(service: ServiceDep, movie_id: str) -> Movie:
    return await service.remove_details(movie_id)
