# Lazy annotations: the `list` method below would otherwise shadow the builtin in later hints.
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.db import aggregations
from app.db.photos import PhotoStore

MEALS = "meals"
FOODS = "foods"
SEARCH_CACHE = "food_search_cache"
PHOTO_BUCKET = "meal_photos"
SEARCH_CACHE_TTL = timedelta(days=30)

MEAL_SORT = [("eaten_on", DESCENDING), ("created_at", DESCENDING)]

Document = dict[str, Any]


class MealRepository:
    """Meals and their photos. `eaten_on` is a `YYYY-MM-DD` string."""

    def __init__(self, db: AsyncDatabase) -> None:
        self.collection = db[MEALS]
        self.photos = PhotoStore(db, PHOTO_BUCKET)

    async def ensure_indexes(self) -> None:
        await self.collection.create_index(MEAL_SORT)

    async def list(self, limit: int, offset: int) -> tuple[list[Document], int]:
        cursor = self.collection.find({}).sort(MEAL_SORT).skip(offset).limit(limit)
        return await cursor.to_list(), await self.collection.count_documents({})

    async def count_by_day(self, start: str, end: str) -> dict[str, int]:
        return await aggregations.count_by_day(self.collection, "eaten_on", start, end)

    async def list_on_day(self, day: str) -> list[Document]:
        cursor = self.collection.find({"eaten_on": day}).sort("created_at", ASCENDING)
        return await cursor.to_list()

    async def get(self, meal_id: ObjectId) -> Document | None:
        return await self.collection.find_one({"_id": meal_id})

    async def create(self, data: Document) -> Document:
        result = await self.collection.insert_one(data)
        return {**data, "_id": result.inserted_id}

    async def update(self, meal_id: ObjectId, changes: Document) -> Document | None:
        return await self.collection.find_one_and_update(
            {"_id": meal_id}, {"$set": changes}, return_document=ReturnDocument.AFTER
        )

    async def delete(self, meal_id: ObjectId) -> Document | None:
        return await self.collection.find_one_and_delete({"_id": meal_id})


class SavedFoodRepository:
    """ "My foods": every food used in a meal, for instant reuse."""

    def __init__(self, db: AsyncDatabase) -> None:
        self.collection = db[FOODS]

    async def ensure_indexes(self) -> None:
        await self.collection.create_index("key", unique=True)
        await self.collection.create_index(
            [("use_count", DESCENDING), ("last_used_at", DESCENDING)]
        )

    async def search(self, pattern: str | None, limit: int) -> list[Document]:
        filter_: Document = {}
        if pattern:
            filter_ = {
                "$or": [
                    {"name": {"$regex": pattern, "$options": "i"}},
                    {"brand": {"$regex": pattern, "$options": "i"}},
                ]
            }
        cursor = (
            self.collection.find(filter_)
            .sort([("use_count", DESCENDING), ("last_used_at", DESCENDING)])
            .limit(limit)
        )
        return await cursor.to_list()

    async def remember(self, key: str, food: Document, used_at: datetime) -> None:
        await self.collection.update_one(
            {"key": key},
            {"$set": {**food, "last_used_at": used_at}, "$inc": {"use_count": 1}},
            upsert=True,
        )


class SearchCacheRepository:
    def __init__(self, db: AsyncDatabase) -> None:
        self.collection = db[SEARCH_CACHE]

    async def ensure_indexes(self) -> None:
        await self.collection.create_index("query", unique=True)
        await self.collection.create_index(
            "fetched_at", expireAfterSeconds=int(SEARCH_CACHE_TTL.total_seconds())
        )

    async def get(self, query: str, now: datetime) -> list[Document] | None:
        doc = await self.collection.find_one(
            {"query": query, "fetched_at": {"$gt": now - SEARCH_CACHE_TTL}}
        )
        return doc["results"] if doc else None

    async def put(self, query: str, results: list[Document], now: datetime) -> None:
        await self.collection.update_one(
            {"query": query}, {"$set": {"results": results, "fetched_at": now}}, upsert=True
        )
