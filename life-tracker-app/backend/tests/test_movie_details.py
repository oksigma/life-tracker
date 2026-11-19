import asyncio
from collections.abc import Iterator
from datetime import date
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.movies.schemas import MovieDetails, TmdbMatch
from app.modules.movies.tmdb import (
    API_URL,
    TmdbClient,
    TmdbError,
    TmdbNotFoundError,
    best_match,
    get_tmdb,
)

TODAY = date.today().isoformat()

DUNE_2021 = MovieDetails(
    tmdb_id=438631,
    title="Dune",
    year=2021,
    release_date="2021-09-15",
    poster_path="/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
    overview="Paul Atreides, a brilliant and gifted young man...",
    runtime=155,
    genres=["Science Fiction", "Adventure"],
)
DUNE_1984 = MovieDetails(
    tmdb_id=841, title="Dune", year=1984, runtime=137, genres=["Science Fiction"]
)
ARRIVAL = MovieDetails(tmdb_id=329865, title="Arrival", year=2016, runtime=116, genres=["Drama"])
DUNE_PART_TWO = MovieDetails(tmdb_id=693134, title="Dune: Part Two", year=2024, runtime=167)


class FakeTmdb:
    def __init__(self) -> None:
        self.movies = {m.tmdb_id: m for m in (DUNE_PART_TWO, DUNE_2021, DUNE_1984, ARRIVAL)}
        self.error: Exception | None = None
        self.searches: list[tuple[str, int | None]] = []

    async def search(self, query: str, year: int | None = None) -> list[TmdbMatch]:
        self.searches.append((query, year))
        if self.error:
            raise self.error
        words = query.lower().split()
        return [
            TmdbMatch(**m.model_dump(include=set(TmdbMatch.model_fields)))
            for m in self.movies.values()
            if all(w in m.title.lower() for w in words) and (year is None or m.year == year)
        ]

    async def details(self, tmdb_id: int) -> MovieDetails:
        if self.error:
            raise self.error
        if tmdb_id not in self.movies:
            raise TmdbNotFoundError
        return self.movies[tmdb_id]


@pytest.fixture
def tmdb(client: TestClient) -> Iterator[FakeTmdb]:
    fake = FakeTmdb()
    app.dependency_overrides[get_tmdb] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_tmdb, None)


def create(client: TestClient, **body: Any) -> dict[str, Any]:
    response = client.post("/api/movies", json={"watched_on": TODAY} | body)
    assert response.status_code == 201, response.text
    return response.json()


# ---------- without a key ----------


def test_status_without_key(client: TestClient) -> None:
    assert client.get("/api/movies/tmdb/status").json() == {"configured": False}


def test_movie_saves_without_key(client: TestClient) -> None:
    movie = create(client, title="Dune")
    assert movie["details"] is None
    assert movie["year"] is None


def test_search_and_attach_need_key(client: TestClient) -> None:
    response = client.get("/api/movies/tmdb/search", params={"q": "dune"})
    assert response.status_code == 503
    assert "TMDB_API_KEY" in response.json()["detail"]
    movie = create(client, title="Dune")
    assert client.post(f"/api/movies/{movie['id']}/details", json={}).status_code == 503


# ---------- with TMDB ----------


def test_status_with_key(client: TestClient, tmdb: FakeTmdb) -> None:
    assert client.get("/api/movies/tmdb/status").json() == {"configured": True}


def test_search(client: TestClient, tmdb: FakeTmdb) -> None:
    body = client.get("/api/movies/tmdb/search", params={"q": "dune"}).json()
    assert [(r["title"], r["year"]) for r in body["results"]] == [
        ("Dune: Part Two", 2024),
        ("Dune", 2021),
        ("Dune", 1984),
    ]
    assert body["results"][1]["poster_path"] == DUNE_2021.poster_path


def test_search_validates_query(client: TestClient, tmdb: FakeTmdb) -> None:
    assert client.get("/api/movies/tmdb/search", params={"q": "d"}).status_code == 422


def test_create_with_picked_movie(client: TestClient, tmdb: FakeTmdb) -> None:
    movie = create(client, title="Dune", tmdb_id=438631)
    assert movie["details"]["tmdb_id"] == 438631
    assert movie["details"]["runtime"] == 155
    assert movie["details"]["genres"] == ["Science Fiction", "Adventure"]
    assert movie["details"]["overview"].startswith("Paul Atreides")
    assert movie["year"] == 2021  # filled from TMDB
    assert "tmdb_id" not in movie
    assert tmdb.searches == []  # picked, so no search needed


def test_create_auto_matches_exact_title(client: TestClient, tmdb: FakeTmdb) -> None:
    # "Dune: Part Two" is the top search result, but the exact title "Dune" wins.
    assert create(client, title="dune")["details"]["tmdb_id"] in (438631, 841)
    assert create(client, title="Arrival")["details"]["tmdb_id"] == 329865


def test_create_auto_match_uses_year(client: TestClient, tmdb: FakeTmdb) -> None:
    assert create(client, title="Dune", year=1984)["details"]["tmdb_id"] == 841


def test_wrong_year_falls_back_to_title(client: TestClient, tmdb: FakeTmdb) -> None:
    movie = create(client, title="Arrival", year=2001)
    assert movie["details"]["tmdb_id"] == 329865
    assert movie["year"] == 2001  # the user's year is kept


def test_no_match_saves_without_details(client: TestClient, tmdb: FakeTmdb) -> None:
    assert create(client, title="My holiday video")["details"] is None


def test_tmdb_failure_never_blocks_saving(client: TestClient, tmdb: FakeTmdb) -> None:
    tmdb.error = TmdbError("down")
    movie = create(client, title="Dune")
    assert movie["details"] is None
    assert client.get("/api/movies").json()["total"] == 1


def test_attach_details_to_existing_movie(client: TestClient) -> None:
    movie = create(client, title="Arrival")  # logged before TMDB was set up
    fake = FakeTmdb()
    app.dependency_overrides[get_tmdb] = lambda: fake
    try:
        updated = client.post(f"/api/movies/{movie['id']}/details", json={}).json()
    finally:
        app.dependency_overrides.pop(get_tmdb, None)
    assert updated["details"]["tmdb_id"] == 329865
    assert updated["year"] == 2016
    assert client.get(f"/api/movies/{movie['id']}").json()["details"]["runtime"] == 116


def test_change_match(client: TestClient, tmdb: FakeTmdb) -> None:
    movie = create(client, title="Dune", year=2021)
    assert movie["details"]["tmdb_id"] == 438631
    updated = client.post(f"/api/movies/{movie['id']}/details", json={"tmdb_id": 841}).json()
    assert updated["details"]["tmdb_id"] == 841
    assert updated["year"] == 2021  # an existing year isn't overwritten


def test_attach_unknown_tmdb_id(client: TestClient, tmdb: FakeTmdb) -> None:
    movie = create(client, title="Dune")
    assert (
        client.post(f"/api/movies/{movie['id']}/details", json={"tmdb_id": 99}).status_code == 404
    )


def test_attach_when_nothing_matches(client: TestClient, tmdb: FakeTmdb) -> None:
    movie = create(client, title="My holiday video")
    response = client.post(f"/api/movies/{movie['id']}/details", json={})
    assert response.status_code == 404
    assert "TMDB" in response.json()["detail"]


def test_attach_when_tmdb_down(client: TestClient, tmdb: FakeTmdb) -> None:
    movie = create(client, title="Dune")
    tmdb.error = TmdbError("down")
    assert client.post(f"/api/movies/{movie['id']}/details", json={}).status_code == 502


def test_remove_details(client: TestClient, tmdb: FakeTmdb) -> None:
    movie = create(client, title="Arrival")
    updated = client.delete(f"/api/movies/{movie['id']}/details").json()
    assert updated["details"] is None
    assert updated["year"] == 2016  # the year stays
    assert client.get(f"/api/movies/{movie['id']}").json()["details"] is None


def test_details_endpoints_404_for_missing_movie(client: TestClient, tmdb: FakeTmdb) -> None:
    missing = "507f1f77bcf86cd799439011"
    assert client.post(f"/api/movies/{missing}/details", json={}).status_code == 404
    assert client.delete(f"/api/movies/{missing}/details").status_code == 404


# ---------- matching ----------


def match(title: str, year: int | None, tmdb_id: int) -> TmdbMatch:
    return TmdbMatch(tmdb_id=tmdb_id, title=title, year=year)


def test_best_match() -> None:
    results = [match("Dune: Part Two", 2024, 1), match("Dune", 2021, 2), match("Dune", 1984, 3)]
    assert best_match(results, "dune", None).tmdb_id == 2
    assert best_match(results, "Dune", 1984).tmdb_id == 3
    assert best_match(results, "Dune Part Two", None).tmdb_id == 1  # punctuation ignored
    assert best_match(results, "Dune Messiah", 2024).tmdb_id == 1  # same year
    assert best_match(results, "Something", None).tmdb_id == 1  # top result
    assert best_match([], "Dune", None) is None


# ---------- client (no network: mocked transport) ----------


def run(handler: Any, credential: str, call: str, *args: Any) -> Any:
    async def go() -> Any:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            return await getattr(TmdbClient(http, credential), call)(*args)

    return asyncio.run(go())


def search_handler(seen: list[httpx.Request]) -> Any:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": 438631,
                        "title": "Dune",
                        "original_title": "Dune",
                        "release_date": "2021-09-15",
                        "poster_path": "/abc_123.jpg",
                        "overview": "Desert planet.",
                    },
                    {
                        "id": 1,
                        "title": "No date",
                        "release_date": "",
                        "poster_path": "javascript:x",
                    },
                    {"title": "No id"},
                ]
            },
        )

    return handler


def test_client_search_with_api_key() -> None:
    seen: list[httpx.Request] = []
    results = run(search_handler(seen), "0123456789abcdef", "search", "dune", 2021)
    assert str(seen[0].url).startswith(f"{API_URL}/search/movie")
    assert seen[0].url.params["api_key"] == "0123456789abcdef"
    assert seen[0].url.params["year"] == "2021"
    assert "authorization" not in seen[0].headers
    assert [(r.tmdb_id, r.year, r.poster_path) for r in results] == [
        (438631, 2021, "/abc_123.jpg"),
        (1, None, None),  # missing date and unsafe poster path are dropped
    ]


def test_client_uses_bearer_for_read_access_token() -> None:
    seen: list[httpx.Request] = []
    run(search_handler(seen), "eyJhbGciOiJIUzI1NiJ9.token", "search", "dune")
    assert seen[0].headers["authorization"] == "Bearer eyJhbGciOiJIUzI1NiJ9.token"
    assert "api_key" not in seen[0].url.params


def test_client_details() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/3/movie/438631"
        return httpx.Response(
            200,
            json={
                "id": 438631,
                "title": "Dune",
                "release_date": "2021-09-15",
                "runtime": 155,
                "genres": [{"id": 878, "name": "Science Fiction"}, {"id": 12, "name": "Adventure"}],
                "overview": "Desert planet.",
            },
        )

    details = run(handler, "key", "details", 438631)
    assert (details.runtime, details.genres, details.release_date) == (
        155,
        ["Science Fiction", "Adventure"],
        "2021-09-15",
    )


@pytest.mark.parametrize(
    ("response", "error"),
    [(httpx.Response(404), TmdbNotFoundError), (httpx.Response(401), TmdbError)],
)
def test_client_errors(response: httpx.Response, error: type[Exception]) -> None:
    with pytest.raises(error):
        run(lambda request: response, "key", "details", 1)


def test_client_offline() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline")

    with pytest.raises(TmdbError):
        run(handler, "key", "search", "dune")
