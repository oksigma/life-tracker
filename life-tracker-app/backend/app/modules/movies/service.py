# Lazy annotations: the `list` method below would otherwise shadow the builtin in later hints.
from __future__ import annotations

from datetime import date
from typing import Any

from bson import ObjectId

from app.core.errors import NotFoundError
from app.core.ids import parse_object_id
from app.core.time import utc_now
from app.modules.movies.repository import Document, MovieRepository
from app.modules.movies.schemas import (
    Movie,
    MovieCreate,
    MovieDetails,
    MovieList,
    MovieUpdate,
    TmdbMatch,
)
from app.modules.movies.tmdb import TmdbClient, TmdbError, TmdbNotConfiguredError, best_match


def _parse_id(movie_id: str) -> ObjectId:
    return parse_object_id(movie_id, "Movie")


def _to_storage(fields: dict[str, Any]) -> dict[str, Any]:
    if isinstance(fields.get("watched_on"), date):
        fields["watched_on"] = fields["watched_on"].isoformat()
    return fields


def _to_movie(doc: Document) -> Movie:
    data = {key: value for key, value in doc.items() if key != "_id"}
    return Movie(id=str(doc["_id"]), **data)


class MovieService:
    def __init__(self, repository: MovieRepository, tmdb: TmdbClient | None = None) -> None:
        self.repository = repository
        self.tmdb = tmdb

    async def list(self, query: str | None, limit: int, offset: int) -> MovieList:
        docs, total = await self.repository.list(query, limit, offset)
        return MovieList(items=[_to_movie(doc) for doc in docs], total=total)

    async def count_by_day(self, start: date, end: date) -> dict[str, int]:
        return await self.repository.count_by_day(start.isoformat(), end.isoformat())

    async def list_on_day(self, day: date) -> list[Movie]:
        return [_to_movie(doc) for doc in await self.repository.list_on_day(day.isoformat())]

    async def get(self, movie_id: str) -> Movie:
        return _to_movie(await self._get_doc(movie_id))

    async def create(self, payload: MovieCreate) -> Movie:
        data = _to_storage(payload.model_dump(exclude={"tmdb_id"}))
        # Details are a bonus: if TMDB is unavailable the movie is still saved.
        try:
            details = await self._find_details(payload.title, payload.year, payload.tmdb_id)
        except TmdbError:
            details = None
        if details is not None:
            data["details"] = details.model_dump()
            if data.get("year") is None:
                data["year"] = details.year
        now = utc_now()
        data |= {"created_at": now, "updated_at": now}
        return _to_movie(await self.repository.create(data))

    async def update(self, movie_id: str, payload: MovieUpdate) -> Movie:
        object_id = _parse_id(movie_id)
        changes = _to_storage(payload.model_dump(exclude_unset=True))
        if not changes:
            return await self.get(movie_id)
        changes["updated_at"] = utc_now()
        doc = await self.repository.update(object_id, changes)
        if doc is None:
            raise NotFoundError("Movie")
        return _to_movie(doc)

    async def delete(self, movie_id: str) -> None:
        if not await self.repository.delete(_parse_id(movie_id)):
            raise NotFoundError("Movie")

    # ---------- TMDB ----------

    async def search_tmdb(self, query: str, year: int | None) -> list[TmdbMatch]:
        return await self._require_tmdb().search(query, year)

    async def attach_details(self, movie_id: str, tmdb_id: int | None) -> Movie:
        """Match a movie to TMDB (a given TMDB id, or the best match for its title).
        Raises NotFoundError if nothing matches; TmdbError if TMDB fails."""
        self._require_tmdb()
        doc = await self._get_doc(movie_id)
        details = await self._find_details(doc["title"], doc.get("year"), tmdb_id)
        if details is None:
            raise NotFoundError("Matching movie on TMDB")
        changes: Document = {"details": details.model_dump(), "updated_at": utc_now()}
        if doc.get("year") is None:
            changes["year"] = details.year
        updated = await self.repository.update(doc["_id"], changes)
        if updated is None:
            raise NotFoundError("Movie")
        return _to_movie(updated)

    async def remove_details(self, movie_id: str) -> Movie:
        doc = await self.repository.update(
            _parse_id(movie_id), {"details": None, "updated_at": utc_now()}
        )
        if doc is None:
            raise NotFoundError("Movie")
        return _to_movie(doc)

    async def _find_details(
        self, title: str, year: int | None, tmdb_id: int | None
    ) -> MovieDetails | None:
        if self.tmdb is None:
            return None
        if tmdb_id is None:
            match = best_match(await self.tmdb.search(title, year), title, year)
            if match is None and year is not None:
                # The year might be wrong; try the title alone.
                match = best_match(await self.tmdb.search(title), title, None)
            if match is None:
                return None
            tmdb_id = match.tmdb_id
        return await self.tmdb.details(tmdb_id)

    def _require_tmdb(self) -> TmdbClient:
        if self.tmdb is None:
            raise TmdbNotConfiguredError
        return self.tmdb

    async def _get_doc(self, movie_id: str) -> Document:
        doc = await self.repository.get(_parse_id(movie_id))
        if doc is None:
            raise NotFoundError("Movie")
        return doc
