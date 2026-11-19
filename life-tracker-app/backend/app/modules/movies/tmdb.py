"""Client for The Movie Database (TMDB) API v3: https://developer.themoviedb.org/docs

Only movie titles and years are sent. Works with either a v3 API key or a v4 "API Read Access
Token" (a JWT, sent as a bearer token).
"""

import re
from typing import Any

import httpx
from fastapi import Request

from app.modules.movies.schemas import MovieDetails, TmdbMatch

API_URL = "https://api.themoviedb.org/3"
MAX_SEARCH_RESULTS = 10
POSTER_PATH = re.compile(r"^/[A-Za-z0-9_-]+\.(jpg|jpeg|png|webp)$")


class TmdbError(Exception):
    """TMDB couldn't be reached or returned something unusable."""


class TmdbNotFoundError(TmdbError):
    pass


class TmdbNotConfiguredError(Exception):
    """No TMDB API key is set."""


class TmdbClient:
    def __init__(self, http: httpx.AsyncClient, credential: str) -> None:
        self.http = http
        credential = credential.strip()
        # v4 read access tokens are JWTs ("eyJ..."); v3 API keys are 32 hex characters.
        if credential.startswith("eyJ"):
            self.headers = {"Authorization": f"Bearer {credential}"}
            self.auth_params: dict[str, str] = {}
        else:
            self.headers = {}
            self.auth_params = {"api_key": credential}

    async def search(self, query: str, year: int | None = None) -> list[TmdbMatch]:
        params: dict[str, Any] = {"query": query, "include_adult": "false"}
        if year:
            params["year"] = year
        data = await self._get("/search/movie", params)
        results = data.get("results") or []
        matches = [m for r in results if isinstance(r, dict) and (m := _parse_match(r))]
        return matches[:MAX_SEARCH_RESULTS]

    async def details(self, tmdb_id: int) -> MovieDetails:
        data = await self._get(f"/movie/{tmdb_id}", {})
        details = _parse_details(data)
        if details is None:
            raise TmdbError("unexpected response")
        return details

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await self.http.get(
                f"{API_URL}{path}", params={**params, **self.auth_params}, headers=self.headers
            )
        except httpx.HTTPError as exc:
            raise TmdbError(str(exc)) from exc
        if response.status_code == 404:
            raise TmdbNotFoundError
        if response.status_code != 200:
            raise TmdbError(f"HTTP {response.status_code}")
        try:
            data = response.json()
        except ValueError as exc:
            raise TmdbError("invalid JSON") from exc
        if not isinstance(data, dict):
            raise TmdbError("unexpected response")
        return data


def _year(release_date: Any) -> int | None:
    if isinstance(release_date, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", release_date):
        return int(release_date[:4])
    return None


def _poster(path: Any) -> str | None:
    return path if isinstance(path, str) and POSTER_PATH.match(path) else None


def _text(value: Any, limit: int) -> str | None:
    return (str(value).strip()[:limit] or None) if value else None


def _parse_match(data: dict[str, Any]) -> TmdbMatch | None:
    if not isinstance(data.get("id"), int) or not data.get("title"):
        return None
    return TmdbMatch(
        tmdb_id=data["id"],
        title=str(data["title"])[:300],
        original_title=_text(data.get("original_title"), 300),
        year=_year(data.get("release_date")),
        poster_path=_poster(data.get("poster_path")),
        overview=_text(data.get("overview"), 5000),
    )


def _parse_details(data: dict[str, Any]) -> MovieDetails | None:
    match = _parse_match(data)
    if match is None:
        return None
    runtime = data.get("runtime")
    genres = [
        str(g["name"])[:50]
        for g in data.get("genres") or []
        if isinstance(g, dict) and g.get("name")
    ]
    release_date = data.get("release_date")
    return MovieDetails(
        **match.model_dump(),
        release_date=release_date if _year(release_date) else None,
        runtime=runtime if isinstance(runtime, int) and runtime > 0 else None,
        genres=genres[:10],
    )


def _normalise(title: str | None) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", (title or "").lower()))


def best_match(results: list[TmdbMatch], title: str, year: int | None) -> TmdbMatch | None:
    """Pick the most likely movie: exact title (and year, if known), then same year,
    then the top result."""
    wanted = _normalise(title)

    def same_title(m: TmdbMatch) -> bool:
        return wanted in (_normalise(m.title), _normalise(m.original_title))

    if year is not None:
        for m in results:
            if same_title(m) and m.year == year:
                return m
        for m in results:
            if m.year == year:
                return m
    for m in results:
        if same_title(m):
            return m
    return results[0] if results else None


def get_tmdb(request: Request) -> TmdbClient | None:
    """FastAPI dependency: the TMDB client, or None if no API key is configured."""
    return request.app.state.tmdb
