from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

TODAY = date.today().isoformat()


def create(client: TestClient, **overrides: Any) -> dict[str, Any]:
    body = {"title": "The Matrix", "watched_on": TODAY} | overrides
    response = client.post("/api/movies", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def test_list_is_empty_initially(client: TestClient) -> None:
    response = client.get("/api/movies")
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


def test_create_with_title_and_date_only(client: TestClient) -> None:
    movie = create(client, title="  Arrival  ")
    assert movie["title"] == "Arrival"
    assert movie["watched_on"] == TODAY
    assert movie["year"] is None
    assert movie["rating"] is None
    assert movie["where"] is None
    assert movie["notes"] is None
    assert movie["id"]
    assert movie["created_at"] == movie["updated_at"]


def test_create_with_all_fields(client: TestClient) -> None:
    movie = create(client, title="Dune", year=2021, rating=4, where="cinema", notes="Huge sound.")
    assert movie | {"id": None, "created_at": None, "updated_at": None} == {
        "id": None,
        "title": "Dune",
        "watched_on": TODAY,
        "year": 2021,
        "rating": 4,
        "where": "cinema",
        "notes": "Huge sound.",
        "details": None,  # no TMDB key in tests
        "created_at": None,
        "updated_at": None,
    }


@pytest.mark.parametrize(
    "overrides",
    [
        {"title": ""},
        {"title": "   "},
        {"title": "x" * 201},
        {"watched_on": (date.today() + timedelta(days=3)).isoformat()},
        {"rating": 0},
        {"rating": 6},
        {"year": 1887},
        {"year": datetime.now(UTC).year + 2},
        {"where": "drive-in"},
        {"notes": "x" * 2001},
    ],
)
def test_create_rejects_invalid_input(client: TestClient, overrides: dict[str, Any]) -> None:
    body = {"title": "The Matrix", "watched_on": TODAY} | overrides
    response = client.post("/api/movies", json=body)
    assert response.status_code == 422
    assert client.get("/api/movies").json()["total"] == 0


def test_create_requires_title_and_date(client: TestClient) -> None:
    assert client.post("/api/movies", json={"watched_on": TODAY}).status_code == 422
    assert client.post("/api/movies", json={"title": "Heat"}).status_code == 422


def test_empty_notes_are_stored_as_null(client: TestClient) -> None:
    assert create(client, notes="   ")["notes"] is None


def test_list_is_newest_first(client: TestClient) -> None:
    create(client, title="Old", watched_on="2020-01-01")
    create(client, title="Newest", watched_on=TODAY)
    create(client, title="Middle", watched_on="2023-06-15")
    titles = [m["title"] for m in client.get("/api/movies").json()["items"]]
    assert titles == ["Newest", "Middle", "Old"]


def test_search_is_case_insensitive_partial_match(client: TestClient) -> None:
    create(client, title="The Matrix")
    create(client, title="The Matrix Reloaded")
    create(client, title="Heat")
    body = client.get("/api/movies", params={"q": "MATRIX"}).json()
    assert body["total"] == 2
    assert {m["title"] for m in body["items"]} == {"The Matrix", "The Matrix Reloaded"}


def test_search_treats_regex_characters_literally(client: TestClient) -> None:
    create(client, title="Heat")
    assert client.get("/api/movies", params={"q": ".*"}).json()["total"] == 0


def test_pagination(client: TestClient) -> None:
    for day in range(1, 6):
        create(client, title=f"Movie {day}", watched_on=f"2024-01-0{day}")
    body = client.get("/api/movies", params={"limit": 2, "offset": 1}).json()
    assert body["total"] == 5
    assert [m["title"] for m in body["items"]] == ["Movie 4", "Movie 3"]


def test_rewatch_creates_separate_entries(client: TestClient) -> None:
    create(client, title="Heat", watched_on="2022-01-01")
    create(client, title="Heat", watched_on="2024-01-01")
    assert client.get("/api/movies", params={"q": "heat"}).json()["total"] == 2


def test_get_one(client: TestClient) -> None:
    movie = create(client)
    response = client.get(f"/api/movies/{movie['id']}")
    assert response.status_code == 200
    assert response.json() == movie


@pytest.mark.parametrize("movie_id", ["not-an-id", "507f1f77bcf86cd799439011"])
def test_missing_or_invalid_id_returns_404(client: TestClient, movie_id: str) -> None:
    assert client.get(f"/api/movies/{movie_id}").status_code == 404
    assert client.patch(f"/api/movies/{movie_id}", json={"rating": 3}).status_code == 404
    assert client.delete(f"/api/movies/{movie_id}").status_code == 404


def test_update_changes_only_given_fields(client: TestClient) -> None:
    movie = create(client, rating=2, notes="Meh")
    response = client.patch(f"/api/movies/{movie['id']}", json={"rating": 5})
    assert response.status_code == 200
    updated = response.json()
    assert updated["rating"] == 5
    assert updated["notes"] == "Meh"
    assert updated["title"] == movie["title"]
    assert updated["updated_at"] > movie["updated_at"]
    assert client.get("/api/movies").json()["items"][0]["rating"] == 5


def test_update_can_clear_optional_fields(client: TestClient) -> None:
    movie = create(client, rating=3, where="home")
    updated = client.patch(f"/api/movies/{movie['id']}", json={"rating": None, "where": None})
    assert updated.json()["rating"] is None
    assert updated.json()["where"] is None


@pytest.mark.parametrize(
    "body", [{"title": None}, {"watched_on": None}, {"title": ""}, {"rating": 9}]
)
def test_update_rejects_invalid_input(client: TestClient, body: dict[str, Any]) -> None:
    movie = create(client)
    assert client.patch(f"/api/movies/{movie['id']}", json=body).status_code == 422


def test_update_with_empty_body_returns_movie_unchanged(client: TestClient) -> None:
    movie = create(client)
    response = client.patch(f"/api/movies/{movie['id']}", json={})
    assert response.status_code == 200
    assert response.json() == movie


def test_delete(client: TestClient) -> None:
    movie = create(client)
    assert client.delete(f"/api/movies/{movie['id']}").status_code == 204
    assert client.get(f"/api/movies/{movie['id']}").status_code == 404
    assert client.get("/api/movies").json()["total"] == 0
