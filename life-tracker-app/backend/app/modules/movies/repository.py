# Lazy annotations: the `list` method below would otherwise shadow the builtin in later hints.
from __future__ import annotations

import re
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.db import aggregations

COLLECTION = "movies_seen"

# Newest viewing first; entries on the same day ordered by when they were logged.
SORT = [("watched_on", DESCENDING), ("created_at", DESCENDING)]

Document = dict[str, Any]


class MovieRepository:
    """MongoDB access for movie viewings. `watched_on` is stored as a `YYYY-MM-DD` string."""

    def __init__(self, db: AsyncDatabase) -> None:
        self.collection = db[COLLECTION]

    async def ensure_indexes(self) -> None:
        await self.collection.create_index(SORT)
        await self.collection.create_index([("title", ASCENDING)])

    async def list(self, query: str | None, limit: int, offset: int) -> tuple[list[Document], int]:
        filter_: Document = {}
        if query:
            filter_["title"] = {"$regex": re.escape(query), "$options": "i"}
        cursor = self.collection.find(filter_).sort(SORT).skip(offset).limit(limit)
        items = await cursor.to_list()
        total = await self.collection.count_documents(filter_)
        return items, total

    async def count_by_day(self, start: str, end: str) -> dict[str, int]:
        return await aggregations.count_by_day(self.collection, "watched_on", start, end)

    async def list_on_day(self, day: str) -> list[Document]:
        cursor = self.collection.find({"watched_on": day}).sort("created_at", ASCENDING)
        return await cursor.to_list()

    async def get(self, movie_id: ObjectId) -> Document | None:
        return await self.collection.find_one({"_id": movie_id})

    async def create(self, data: Document) -> Document:
        result = await self.collection.insert_one(data)
        return {**data, "_id": result.inserted_id}

    async def update(self, movie_id: ObjectId, changes: Document) -> Document | None:
        return await self.collection.find_one_and_update(
            {"_id": movie_id}, {"$set": changes}, return_document=ReturnDocument.AFTER
        )

    async def delete(self, movie_id: ObjectId) -> bool:
        result = await self.collection.delete_one({"_id": movie_id})
        return result.deleted_count == 1
