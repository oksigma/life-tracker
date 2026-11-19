"""Client for the Open Food Facts food database (https://world.openfoodfacts.org).

Only the search words are sent. Open Food Facts allows 10 searches per minute per IP, so searches
are rate-limited here (and cached by the service) to make sure the app never gets blocked.
"""

import time
from collections import deque
from typing import Any, Protocol

import httpx
from fastapi import Request

from app.modules.food.schemas import FoodOption

SEARCH_URL = "https://search.openfoodfacts.org/search"
LEGACY_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
FIELDS = "code,product_name,brands,serving_size,nutriments"
PAGE_SIZE = 40
MAX_RESULTS = 20
KJ_PER_KCAL = 4.184


class FoodDatabaseError(Exception):
    """The food database couldn't be reached or returned something unusable."""


class FoodDatabaseRateLimitedError(FoodDatabaseError):
    """Too many searches in the last minute."""


class FoodDatabase(Protocol):
    async def search(self, query: str) -> list[FoodOption]: ...


class RateLimiter:
    """Allows at most `max_calls` per `period` seconds (sliding window)."""

    def __init__(self, max_calls: int, period: float = 60.0) -> None:
        self.max_calls = max_calls
        self.period = period
        self.calls: deque[float] = deque()

    def acquire(self) -> None:
        now = time.monotonic()
        while self.calls and now - self.calls[0] >= self.period:
            self.calls.popleft()
        if len(self.calls) >= self.max_calls:
            raise FoodDatabaseRateLimitedError
        self.calls.append(now)


class OpenFoodFactsClient:
    def __init__(self, http: httpx.AsyncClient, limiter: RateLimiter) -> None:
        self.http = http
        self.limiter = limiter

    async def search(self, query: str) -> list[FoodOption]:
        self.limiter.acquire()
        try:
            data = await self._get(
                SEARCH_URL, {"q": query, "page_size": PAGE_SIZE, "fields": FIELDS}
            )
            products = data.get("hits", [])
        except FoodDatabaseRateLimitedError:
            raise
        except FoodDatabaseError:
            # The newer search service is unavailable: fall back to the legacy full-text search.
            data = await self._get(
                LEGACY_SEARCH_URL,
                {
                    "search_terms": query,
                    "search_simple": 1,
                    "action": "process",
                    "json": 1,
                    "page_size": PAGE_SIZE,
                    "fields": FIELDS,
                },
            )
            products = data.get("products", [])
        return parse_products(products)

    async def _get(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await self.http.get(url, params=params)
        except httpx.HTTPError as exc:
            raise FoodDatabaseError(str(exc)) from exc
        if response.status_code == 429:
            raise FoodDatabaseRateLimitedError
        if response.status_code != 200:
            raise FoodDatabaseError(f"HTTP {response.status_code}")
        try:
            data = response.json()
        except ValueError as exc:
            raise FoodDatabaseError("invalid JSON") from exc
        if not isinstance(data, dict):
            raise FoodDatabaseError("unexpected response")
        return data


def parse_products(products: list[Any]) -> list[FoodOption]:
    """Turn Open Food Facts products into food options, skipping any without calorie data."""
    results: list[FoodOption] = []
    seen: set[str] = set()
    for product in products:
        if not isinstance(product, dict):
            continue
        option = _parse_product(product)
        if option is None:
            continue
        key = option.off_code or f"{option.name}|{option.brand}".lower()
        if key in seen:
            continue
        seen.add(key)
        results.append(option)
        if len(results) == MAX_RESULTS:
            break
    return results


def _parse_product(product: dict[str, Any]) -> FoodOption | None:
    name = str(product.get("product_name") or "").strip()
    if not name:
        return None
    nutriments = product.get("nutriments") or {}
    per_100g = _kcal(nutriments, "100g")
    per_serving = _kcal(nutriments, "serving")
    if per_100g is None and per_serving is None:
        return None
    return FoodOption(
        name=name[:200],
        brand=_first_brand(product.get("brands")),
        kcal_per_100g=per_100g,
        kcal_per_serving=per_serving,
        serving_size=(str(product.get("serving_size") or "").strip() or None),
        source="openfoodfacts",
        off_code=(str(product.get("code") or "").strip()[:32] or None),
    )


def _kcal(nutriments: dict[str, Any], basis: str) -> float | None:
    """kcal for a basis ("100g" or "serving"), converting from kJ if only that is given."""
    value = _number(nutriments.get(f"energy-kcal_{basis}"))
    if value is None:
        kj = _number(nutriments.get(f"energy-kj_{basis}"))
        value = kj / KJ_PER_KCAL if kj is not None else None
    if value is None or value < 0 or (basis == "100g" and value > 1000):
        return None  # missing or implausible
    return round(value, 1)


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None and value != "" else None
    except (TypeError, ValueError):
        return None


def _first_brand(brands: Any) -> str | None:
    if isinstance(brands, list):
        brands = brands[0] if brands else None
    if not brands:
        return None
    return str(brands).split(",")[0].strip()[:200] or None


def get_food_database(request: Request) -> FoodDatabase:
    """FastAPI dependency: the shared client created in the app's lifespan."""
    return request.app.state.food_database
