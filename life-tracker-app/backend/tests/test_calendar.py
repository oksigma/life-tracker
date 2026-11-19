from datetime import date, timedelta
from io import BytesIO
from typing import Any

import pytest
from fastapi.testclient import TestClient
from PIL import Image

URL = "/api/calendar"


def jpeg() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (60, 80), (90, 90, 90)).save(buffer, format="JPEG")
    return buffer.getvalue()


def add_movie(client: TestClient, day: str, title: str = "Heat") -> dict[str, Any]:
    response = client.post("/api/movies", json={"title": title, "watched_on": day})
    assert response.status_code == 201
    return response.json()


def add_outfit(client: TestClient, day: str) -> dict[str, Any]:
    response = client.post(
        "/api/clothing/outfits",
        files={"photo": ("o.jpg", jpeg(), "image/jpeg")},
        data={"worn_on": day},
    )
    assert response.status_code == 201
    return response.json()


def month(client: TestClient, start: str = "2025-11-01", end: str = "2025-11-30") -> Any:
    response = client.get(URL, params={"start": start, "end": end})
    assert response.status_code == 200, response.text
    return response.json()


def test_empty_range(client: TestClient) -> None:
    assert month(client) == {"start": "2025-11-01", "end": "2025-11-30", "days": []}


def test_counts_per_area_per_day(client: TestClient) -> None:
    add_movie(client, "2025-11-10")
    add_outfit(client, "2025-11-10")
    add_outfit(client, "2025-11-10")
    add_outfit(client, "2025-11-03")
    add_movie(client, "2025-11-12")
    add_movie(client, "2025-11-12", "Arrival")
    assert month(client)["days"] == [
        {"date": "2025-11-03", "counts": {"clothing": 1}},
        {"date": "2025-11-10", "counts": {"movies": 1, "clothing": 2}},
        {"date": "2025-11-12", "counts": {"movies": 2}},
    ]


def test_range_is_inclusive_and_excludes_outside_days(client: TestClient) -> None:
    for day in ("2025-10-31", "2025-11-01", "2025-11-30", "2025-12-01"):
        add_movie(client, day)
    days = [d["date"] for d in month(client)["days"]]
    assert days == ["2025-11-01", "2025-11-30"]


def test_changing_outfit_date_moves_it(client: TestClient) -> None:
    outfit = add_outfit(client, "2025-11-05")
    client.patch(f"/api/clothing/outfits/{outfit['id']}", json={"worn_on": "2025-11-20"})
    assert [d["date"] for d in month(client)["days"]] == ["2025-11-20"]


def test_deleted_entries_disappear(client: TestClient) -> None:
    movie = add_movie(client, "2025-11-05")
    client.delete(f"/api/movies/{movie['id']}")
    assert month(client)["days"] == []


@pytest.mark.parametrize(
    "params",
    [
        {"start": "2025-11-30", "end": "2025-11-01"},
        {"start": "2025-01-01", "end": "2026-01-02"},
        {"start": "2026-13-01", "end": "2026-12-31"},
        {"start": "not-a-date", "end": "2025-11-30"},
        {"start": "2025-11-01"},
    ],
)
def test_rejects_invalid_ranges(client: TestClient, params: dict[str, str]) -> None:
    assert client.get(URL, params=params).status_code == 422


def test_full_year_range_is_allowed(client: TestClient) -> None:
    assert client.get(URL, params={"start": "2024-01-01", "end": "2024-12-31"}).status_code == 200


def test_day_entries(client: TestClient) -> None:
    first = add_movie(client, "2025-11-10", "Heat")
    second = add_movie(client, "2025-11-10", "Arrival")
    outfit = add_outfit(client, "2025-11-10")
    add_movie(client, "2025-11-11", "Other day")
    body = client.get(f"{URL}/days/2025-11-10").json()
    assert body["date"] == "2025-11-10"
    assert [m["id"] for m in body["movies"]] == [first["id"], second["id"]]
    assert [o["id"] for o in body["clothing"]] == [outfit["id"]]
    assert body["clothing"][0]["thumbnail_url"] == outfit["thumbnail_url"]


def test_empty_day(client: TestClient) -> None:
    day = (date.today() - timedelta(days=1)).isoformat()
    assert client.get(f"{URL}/days/{day}").json() == {
        "date": day,
        "movies": [],
        "clothing": [],
        "food": [],
    }


def test_day_rejects_invalid_date(client: TestClient) -> None:
    assert client.get(f"{URL}/days/2026-02-30").status_code == 422
