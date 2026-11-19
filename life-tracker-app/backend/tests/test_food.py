import asyncio
import json
from collections.abc import Iterator
from datetime import date, timedelta
from io import BytesIO
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import ExifTags, Image
from pymongo.database import Database

from app.main import app
from app.modules.food.openfoodfacts import (
    LEGACY_SEARCH_URL,
    SEARCH_URL,
    FoodDatabaseError,
    FoodDatabaseRateLimitedError,
    OpenFoodFactsClient,
    RateLimiter,
    get_food_database,
    parse_products,
)
from app.modules.food.schemas import FoodOption

TODAY = date.today().isoformat()
MEALS = "/api/food/meals"

BANANA = {"name": "Banana", "source": "openfoodfacts", "off_code": "123", "kcal_per_100g": 89}


# ---------- fakes & helpers ----------


class FakeFoodDatabase:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.results = [
            FoodOption(name="Banana", kcal_per_100g=89, source="openfoodfacts", off_code="123")
        ]
        self.error: Exception | None = None

    async def search(self, query: str) -> list[FoodOption]:
        self.calls.append(query)
        if self.error:
            raise self.error
        return self.results


@pytest.fixture
def food_db(client: TestClient) -> Iterator[FakeFoodDatabase]:
    fake = FakeFoodDatabase()
    app.dependency_overrides[get_food_database] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_food_database, None)


def jpeg_with_gps() -> bytes:
    exif = Image.Exif()
    exif.get_ifd(ExifTags.IFD.GPSInfo)[ExifTags.GPS.GPSLatitude] = (51.0, 30.0, 0.0)
    buffer = BytesIO()
    Image.new("RGB", (800, 600), (200, 150, 50)).save(buffer, format="JPEG", exif=exif.tobytes())
    return buffer.getvalue()


def post_meal(
    client: TestClient,
    items: list[dict[str, Any]] | str | None = None,
    photo: bytes | None = None,
    **form: str,
) -> Any:
    data = {"meal_type": "lunch", "eaten_on": TODAY} | form
    if items is not None:
        data["items"] = items if isinstance(items, str) else json.dumps(items)
    files = {"photo": ("meal.jpg", photo, "image/jpeg")} if photo is not None else None
    return client.post(MEALS, data=data, files=files)


def create_meal(client: TestClient, items: list[dict[str, Any]] | None = None, **kw: Any) -> Any:
    response = post_meal(client, items if items is not None else [], **kw)
    assert response.status_code == 201, response.text
    return response.json()


# ---------- meals ----------


def test_list_is_empty_initially(client: TestClient) -> None:
    assert client.get(MEALS).json() == {"items": [], "total": 0}


def test_calories_from_grams(client: TestClient) -> None:
    meal = create_meal(client, [BANANA | {"quantity": 120, "unit": "g"}])
    assert meal["items"][0]["kcal"] == 106.8
    assert meal["total_kcal"] == 106.8
    assert meal["photo_url"] is None
    assert meal["thumbnail_url"] is None


def test_calories_from_servings(client: TestClient) -> None:
    item = {"name": "Toast", "kcal_per_serving": 80, "quantity": 2, "unit": "serving"}
    assert create_meal(client, [item])["total_kcal"] == 160


def test_backend_recalculates_and_ignores_client_kcal(client: TestClient) -> None:
    item = BANANA | {"quantity": 100, "unit": "g", "kcal": 5000}
    assert create_meal(client, [item])["items"][0]["kcal"] == 89


def test_manual_calories(client: TestClient) -> None:
    meal = create_meal(
        client,
        [{"name": "Homemade soup", "kcal": 250}, BANANA | {"quantity": 100, "unit": "g"}],
    )
    assert meal["total_kcal"] == 339
    assert meal["items"][0]["source"] == "manual"


def test_meal_without_items_or_photo(client: TestClient) -> None:
    meal = create_meal(client, [], meal_type="snack", notes="Forgot what")
    assert meal["total_kcal"] == 0
    assert meal["items"] == []
    assert meal["meal_type"] == "snack"


def test_defaults_to_today(client: TestClient) -> None:
    response = client.post(MEALS, data={"meal_type": "dinner", "items": "[]"})
    assert response.status_code == 201
    assert response.json()["eaten_on"] == TODAY


@pytest.mark.parametrize(
    ("items", "form"),
    [
        ([{"name": "Mystery"}], {}),  # no kcal and nothing to calculate from
        ([{"name": "Bread", "quantity": 2}], {}),  # quantity without unit
        ([{"name": "Bread", "unit": "g", "kcal": 10}], {}),  # unit without quantity
        ([{"name": "", "kcal": 10}], {}),
        ([{"name": "x", "kcal": -1}], {}),
        ([{"name": "x", "kcal": 10, "unit": "cups", "quantity": 1}], {}),
        ([BANANA | {"quantity": 20_000, "unit": "g"}], {}),  # 17 800 kcal, over the item limit
        ([{"name": "x", "kcal": 1}] * 51, {}),
        ([], {"meal_type": "brunch"}),
        ([], {"eaten_on": (date.today() + timedelta(days=3)).isoformat()}),
        ("not json", {}),
    ],
)
def test_rejects_invalid_meals(client: TestClient, items: Any, form: dict[str, str]) -> None:
    assert post_meal(client, items, **form).status_code == 422
    assert client.get(MEALS).json()["total"] == 0


def test_photo_is_processed_and_stripped(client: TestClient, db: Database) -> None:
    meal = create_meal(client, [], photo=jpeg_with_gps())
    assert meal["photo_url"] == f"{MEALS}/{meal['id']}/photo"
    for url in (meal["photo_url"], meal["thumbnail_url"]):
        response = client.get(url)
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        assert len(Image.open(BytesIO(response.content)).getexif()) == 0
    assert db["meal_photos.files"].count_documents({}) == 2


def test_rejects_non_image_photo(client: TestClient, db: Database) -> None:
    assert post_meal(client, [], photo=b"%PDF not an image").status_code == 415
    assert client.get(MEALS).json()["total"] == 0
    assert db["meal_photos.files"].count_documents({}) == 0


def test_meal_without_photo_has_no_photo_endpoint(client: TestClient) -> None:
    meal = create_meal(client, [])
    assert client.get(f"{MEALS}/{meal['id']}/photo").status_code == 404


def test_list_newest_first(client: TestClient) -> None:
    create_meal(client, [], eaten_on="2025-01-01", meal_type="breakfast")
    create_meal(client, [], eaten_on=TODAY, meal_type="dinner")
    create_meal(client, [], eaten_on="2025-06-01", meal_type="lunch")
    assert [m["eaten_on"] for m in client.get(MEALS).json()["items"]] == [
        TODAY,
        "2025-06-01",
        "2025-01-01",
    ]


def test_update_items_recalculates_total(client: TestClient) -> None:
    meal = create_meal(client, [BANANA | {"quantity": 100, "unit": "g"}])
    response = client.patch(
        f"{MEALS}/{meal['id']}",
        json={"items": [BANANA | {"quantity": 200, "unit": "g"}, {"name": "Tea", "kcal": 20}]},
    )
    assert response.status_code == 200
    assert response.json()["total_kcal"] == 198
    assert client.get(f"{MEALS}/{meal['id']}").json()["total_kcal"] == 198


def test_update_date_type_notes(client: TestClient) -> None:
    meal = create_meal(client, [{"name": "Tea", "kcal": 20}])
    body = client.patch(
        f"{MEALS}/{meal['id']}",
        json={"eaten_on": "2025-05-05", "meal_type": "snack", "notes": "Late"},
    ).json()
    assert (body["eaten_on"], body["meal_type"], body["notes"]) == ("2025-05-05", "snack", "Late")
    assert body["total_kcal"] == 20


@pytest.mark.parametrize(
    "body", [{"eaten_on": None}, {"meal_type": None}, {"items": None}, {"items": [{"name": "x"}]}]
)
def test_update_rejects_invalid(client: TestClient, body: dict[str, Any]) -> None:
    meal = create_meal(client, [])
    assert client.patch(f"{MEALS}/{meal['id']}", json=body).status_code == 422


def test_delete_removes_meal_and_photos(client: TestClient, db: Database) -> None:
    meal = create_meal(client, [], photo=jpeg_with_gps())
    assert client.delete(f"{MEALS}/{meal['id']}").status_code == 204
    assert client.get(f"{MEALS}/{meal['id']}").status_code == 404
    assert db["meal_photos.files"].count_documents({}) == 0
    assert db["meal_photos.chunks"].count_documents({}) == 0


@pytest.mark.parametrize("meal_id", ["nope", "507f1f77bcf86cd799439011"])
def test_missing_meal_404(client: TestClient, meal_id: str) -> None:
    assert client.get(f"{MEALS}/{meal_id}").status_code == 404
    assert client.patch(f"{MEALS}/{meal_id}", json={"notes": "x"}).status_code == 404
    assert client.delete(f"{MEALS}/{meal_id}").status_code == 404


def test_meals_appear_on_calendar(client: TestClient) -> None:
    create_meal(client, [{"name": "Tea", "kcal": 20}], eaten_on="2025-11-10")
    create_meal(client, [], eaten_on="2025-11-10", meal_type="dinner")
    days = client.get("/api/calendar", params={"start": "2025-11-01", "end": "2025-11-30"}).json()
    assert days["days"] == [{"date": "2025-11-10", "counts": {"food": 2}}]
    day = client.get("/api/calendar/days/2025-11-10").json()
    assert [m["total_kcal"] for m in day["food"]] == [20, 0]


# ---------- my foods ----------


def saved(client: TestClient, q: str | None = None) -> list[dict[str, Any]]:
    params = {"q": q} if q is not None else {}
    return client.get("/api/food/foods", params=params).json()["items"]


def test_foods_used_are_remembered(client: TestClient) -> None:
    create_meal(client, [BANANA | {"quantity": 120, "unit": "g"}])
    create_meal(client, [BANANA | {"quantity": 90, "unit": "g"}])
    foods = saved(client, "ban")
    assert len(foods) == 1
    assert foods[0]["name"] == "Banana"
    assert foods[0]["kcal_per_100g"] == 89
    assert foods[0]["use_count"] == 2


def test_manual_food_basis_is_derived(client: TestClient) -> None:
    create_meal(
        client,
        [
            {"name": "Homemade soup", "kcal": 250},
            {"name": "Granola", "kcal": 180, "quantity": 40, "unit": "g"},
            {"name": "Cookie", "kcal": 300, "quantity": 2, "unit": "serving"},
        ],
    )
    by_name = {f["name"]: f for f in saved(client)}
    assert by_name["Homemade soup"]["kcal_per_serving"] == 250
    assert by_name["Granola"]["kcal_per_100g"] == 450
    assert by_name["Cookie"]["kcal_per_serving"] == 150


def test_saved_food_search_matches_brand_and_escapes_regex(client: TestClient) -> None:
    create_meal(client, [{"name": "Oat milk", "brand": "Oatly", "kcal": 50}])
    assert [f["name"] for f in saved(client, "oatly")] == ["Oat milk"]
    assert saved(client, ".*") == []


def test_most_used_foods_first(client: TestClient) -> None:
    create_meal(client, [{"name": "Tea", "kcal": 20}, {"name": "Toast", "kcal": 80}])
    create_meal(client, [{"name": "Toast", "kcal": 80}])
    assert [f["name"] for f in saved(client)] == ["Toast", "Tea"]


# ---------- food database lookup ----------


def test_lookup_returns_results(client: TestClient, food_db: FakeFoodDatabase) -> None:
    body = client.get("/api/food/lookup", params={"q": "  Banana "}).json()
    assert body["cached"] is False
    assert body["results"][0]["kcal_per_100g"] == 89
    assert food_db.calls == ["banana"]


def test_lookup_is_cached(client: TestClient, food_db: FakeFoodDatabase) -> None:
    client.get("/api/food/lookup", params={"q": "banana"})
    second = client.get("/api/food/lookup", params={"q": "BANANA"}).json()
    assert second["cached"] is True
    assert second["results"][0]["name"] == "Banana"
    assert food_db.calls == ["banana"]


def test_lookup_rate_limited(client: TestClient, food_db: FakeFoodDatabase) -> None:
    food_db.error = FoodDatabaseRateLimitedError()
    response = client.get("/api/food/lookup", params={"q": "cheese"})
    assert response.status_code == 429
    assert "10 searches a minute" in response.json()["detail"]


def test_lookup_unreachable(client: TestClient, food_db: FakeFoodDatabase) -> None:
    food_db.error = FoodDatabaseError("down")
    assert client.get("/api/food/lookup", params={"q": "cheese"}).status_code == 502


def test_lookup_requires_query(client: TestClient, food_db: FakeFoodDatabase) -> None:
    assert client.get("/api/food/lookup", params={"q": "a"}).status_code == 422
    assert client.get("/api/food/lookup").status_code == 422


# ---------- Open Food Facts client (no network: mocked transport) ----------


def product(name: str = "Banana", **nutriments: Any) -> dict[str, Any]:
    return {"code": "1", "product_name": name, "brands": "Acme", "nutriments": nutriments}


def test_parse_products() -> None:
    results = parse_products(
        [
            product("Banana", **{"energy-kcal_100g": 89}),
            product("No data"),
            product("Kilojoules only", **{"energy-kj_100g": 418.4}) | {"code": "2"},
            product("", **{"energy-kcal_100g": 50}),
            product("Implausible", **{"energy-kcal_100g": 5000}) | {"code": "3"},
            product("Per serving", **{"energy-kcal_serving": "120"})
            | {"code": "4", "brands": ["Brand A", "Brand B"], "serving_size": "30 g"},
            product("Duplicate", **{"energy-kcal_100g": 1}),  # same code "1" as Banana
            "not a dict",
        ]
    )
    assert [(r.name, r.kcal_per_100g, r.kcal_per_serving, r.brand) for r in results] == [
        ("Banana", 89, None, "Acme"),
        ("Kilojoules only", 100, None, "Acme"),
        ("Per serving", None, 120, "Brand A"),
    ]
    assert results[2].serving_size == "30 g"


def test_rate_limiter() -> None:
    limiter = RateLimiter(max_calls=2, period=60)
    limiter.acquire()
    limiter.acquire()
    with pytest.raises(FoodDatabaseRateLimitedError):
        limiter.acquire()


def run_search(handler: Any, limiter: RateLimiter | None = None) -> list[FoodOption]:
    async def go() -> list[FoodOption]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            client = OpenFoodFactsClient(http, limiter or RateLimiter(10))
            return await client.search("banana")

    return asyncio.run(go())


def test_client_uses_search_service() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith(SEARCH_URL)
        assert request.url.params["q"] == "banana"
        return httpx.Response(200, json={"hits": [product(**{"energy-kcal_100g": 89})]})

    assert [r.name for r in run_search(handler)] == ["Banana"]


def test_client_falls_back_to_legacy_search() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url).startswith(SEARCH_URL):
            return httpx.Response(503)
        assert str(request.url).startswith(LEGACY_SEARCH_URL)
        assert request.url.params["search_terms"] == "banana"
        return httpx.Response(200, json={"products": [product(**{"energy-kcal_100g": 89})]})

    assert [r.name for r in run_search(handler)] == ["Banana"]


def test_client_reports_rate_limit() -> None:
    with pytest.raises(FoodDatabaseRateLimitedError):
        run_search(lambda request: httpx.Response(429))


def test_client_reports_unreachable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline")

    with pytest.raises(FoodDatabaseError):
        run_search(handler)


def test_client_enforces_local_rate_limit_without_calling_api() -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"hits": []})

    limiter = RateLimiter(max_calls=1)
    run_search(handler, limiter)
    with pytest.raises(FoodDatabaseRateLimitedError):
        run_search(handler, limiter)
    assert len(calls) == 1
