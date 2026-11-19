# Lazy annotations: the `list` method below would otherwise shadow the builtin in later hints.
from __future__ import annotations

import asyncio
import re
from datetime import date
from typing import Literal

from bson import ObjectId

from app.core.errors import NotFoundError
from app.core.ids import parse_object_id
from app.core.images import process_photo
from app.core.time import utc_now
from app.modules.food.openfoodfacts import FoodDatabase
from app.modules.food.repository import (
    Document,
    MealRepository,
    SavedFoodRepository,
    SearchCacheRepository,
)
from app.modules.food.schemas import (
    FoodLookup,
    FoodOption,
    Meal,
    MealCreateForm,
    MealItemIn,
    MealList,
    MealUpdate,
    SavedFood,
    SavedFoodList,
)

PhotoSize = Literal["photo", "thumbnail"]


def _parse_id(meal_id: str) -> ObjectId:
    return parse_object_id(meal_id, "Meal")


def _total(items: list[MealItemIn]) -> float:
    return round(sum(item.kcal or 0 for item in items), 1)


def _to_meal(doc: Document) -> Meal:
    meal_id = str(doc["_id"])
    base = f"/api/food/meals/{meal_id}"
    has_photo = doc.get("photo_file_id") is not None
    return Meal(
        id=meal_id,
        eaten_on=doc["eaten_on"],
        meal_type=doc["meal_type"],
        notes=doc.get("notes"),
        items=doc.get("items", []),
        total_kcal=doc.get("total_kcal", 0),
        photo_url=f"{base}/photo" if has_photo else None,
        thumbnail_url=f"{base}/thumbnail" if has_photo else None,
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


def normalise_query(query: str) -> str:
    return " ".join(query.lower().split())


def saved_food_from_item(item: MealItemIn) -> tuple[str, Document]:
    """The "My foods" entry for a meal item: its key and per-unit calorie basis.

    Manual items only have a total, so their basis is derived from the amount entered
    (per 100 g/ml, or per serving; no amount = one serving).
    """
    per_100g, per_serving = item.kcal_per_100g, item.kcal_per_serving
    if (
        item.source == "manual"
        and per_100g is None
        and per_serving is None
        and item.kcal is not None
    ):
        if item.unit in ("g", "ml") and item.quantity:
            per_100g = round(item.kcal / item.quantity * 100, 1)
        else:
            per_serving = round(item.kcal / (item.quantity or 1), 1)
    key = item.off_code or f"{item.name}|{item.brand or ''}".lower()
    return key, {
        "name": item.name,
        "brand": item.brand,
        "kcal_per_100g": per_100g,
        "kcal_per_serving": per_serving,
        "source": item.source,
        "off_code": item.off_code,
    }


class MealService:
    def __init__(self, meals: MealRepository, foods: SavedFoodRepository) -> None:
        self.meals = meals
        self.foods = foods

    async def list(self, limit: int, offset: int) -> MealList:
        docs, total = await self.meals.list(limit, offset)
        return MealList(items=[_to_meal(doc) for doc in docs], total=total)

    async def count_by_day(self, start: date, end: date) -> dict[str, int]:
        return await self.meals.count_by_day(start.isoformat(), end.isoformat())

    async def list_on_day(self, day: date) -> list[Meal]:
        return [_to_meal(doc) for doc in await self.meals.list_on_day(day.isoformat())]

    async def get(self, meal_id: str) -> Meal:
        return _to_meal(await self._get_doc(meal_id))

    async def create(self, form: MealCreateForm, photo: bytes | None) -> Meal:
        eaten_on = form.eaten_on or date.today()
        photo_id = thumbnail_id = None
        if photo is not None:
            processed = await asyncio.to_thread(process_photo, photo)
            photo_id = await self.meals.photos.save(f"meal-{eaten_on}.jpg", processed.full)
            thumbnail_id = await self.meals.photos.save(
                f"meal-{eaten_on}-thumb.jpg", processed.thumbnail
            )
        now = utc_now()
        try:
            doc = await self.meals.create(
                {
                    "eaten_on": eaten_on.isoformat(),
                    "meal_type": form.meal_type,
                    "notes": form.notes,
                    "items": [item.model_dump() for item in form.items],
                    "total_kcal": _total(form.items),
                    "photo_file_id": photo_id,
                    "thumbnail_file_id": thumbnail_id,
                    "created_at": now,
                    "updated_at": now,
                }
            )
        except Exception:
            # Don't leave orphaned photos behind if the meal couldn't be saved.
            for file_id in (photo_id, thumbnail_id):
                if file_id is not None:
                    await self.meals.photos.delete(file_id)
            raise
        await self._remember(form.items)
        return _to_meal(doc)

    async def update(self, meal_id: str, payload: MealUpdate) -> Meal:
        object_id = _parse_id(meal_id)
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            return await self.get(meal_id)
        if changes.get("eaten_on") is not None:
            changes["eaten_on"] = changes["eaten_on"].isoformat()
        if payload.items is not None:
            changes["items"] = [item.model_dump() for item in payload.items]
            changes["total_kcal"] = _total(payload.items)
        changes["updated_at"] = utc_now()
        doc = await self.meals.update(object_id, changes)
        if doc is None:
            raise NotFoundError("Meal")
        if payload.items is not None:
            await self._remember(payload.items)
        return _to_meal(doc)

    async def delete(self, meal_id: str) -> None:
        doc = await self.meals.delete(_parse_id(meal_id))
        if doc is None:
            raise NotFoundError("Meal")
        for field in ("photo_file_id", "thumbnail_file_id"):
            if doc.get(field) is not None:
                await self.meals.photos.delete(doc[field])

    async def read_photo(self, meal_id: str, size: PhotoSize) -> bytes:
        doc = await self._get_doc(meal_id)
        file_id = doc.get("photo_file_id" if size == "photo" else "thumbnail_file_id")
        data = await self.meals.photos.read(file_id) if file_id is not None else None
        if data is None:
            raise NotFoundError("Photo")
        return data

    async def search_saved_foods(self, query: str | None, limit: int) -> SavedFoodList:
        pattern = re.escape(normalise_query(query)) if query and query.strip() else None
        docs = await self.foods.search(pattern, limit)
        return SavedFoodList(
            items=[
                SavedFood(
                    id=str(doc["_id"]),
                    use_count=doc.get("use_count", 0),
                    **{k: doc.get(k) for k in FoodOption.model_fields},
                )
                for doc in docs
            ]
        )

    async def _remember(self, items: list[MealItemIn]) -> None:
        now = utc_now()
        for item in items:
            key, food = saved_food_from_item(item)
            await self.foods.remember(key, food, now)

    async def _get_doc(self, meal_id: str) -> Document:
        doc = await self.meals.get(_parse_id(meal_id))
        if doc is None:
            raise NotFoundError("Meal")
        return doc


class FoodLookupService:
    """Food database search with a 30-day cache, so repeat searches don't use up the rate limit."""

    def __init__(self, database: FoodDatabase, cache: SearchCacheRepository) -> None:
        self.database = database
        self.cache = cache

    async def lookup(self, query: str) -> FoodLookup:
        normalised = normalise_query(query)
        now = utc_now()
        cached = await self.cache.get(normalised, now)
        if cached is not None:
            return FoodLookup(results=[FoodOption(**r) for r in cached], cached=True)
        results = await self.database.search(normalised)
        await self.cache.put(normalised, [r.model_dump() for r in results], now)
        return FoodLookup(results=results, cached=False)
