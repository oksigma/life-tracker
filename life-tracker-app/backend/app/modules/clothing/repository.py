# Lazy annotations: the `list` method below would otherwise shadow the builtin in later hints.
from __future__ import annotations

from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.db import aggregations
from app.db.photos import PhotoStore

COLLECTION = "outfits"
PHOTO_BUCKET = "outfit_photos"

# Newest day first; outfits on the same day ordered by when they were logged.
SORT = [("worn_on", DESCENDING), ("created_at", DESCENDING)]

Document = dict[str, Any]


class OutfitRepository:
    """MongoDB access for outfits and their photos (GridFS). `worn_on` is a `YYYY-MM-DD` string."""

    def __init__(self, db: AsyncDatabase) -> None:
        self.collection = db[COLLECTION]
        self.photos = PhotoStore(db, PHOTO_BUCKET)

    async def ensure_indexes(self) -> None:
        await self.collection.create_index(SORT)

    async def list(self, limit: int, offset: int) -> tuple[list[Document], int]:
        cursor = self.collection.find({}).sort(SORT).skip(offset).limit(limit)
        return await cursor.to_list(), await self.collection.count_documents({})

    async def count_by_day(self, start: str, end: str) -> dict[str, int]:
        return await aggregations.count_by_day(self.collection, "worn_on", start, end)

    async def list_on_day(self, day: str) -> list[Document]:
        cursor = self.collection.find({"worn_on": day}).sort("created_at", ASCENDING)
        return await cursor.to_list()

    async def get(self, outfit_id: ObjectId) -> Document | None:
        return await self.collection.find_one({"_id": outfit_id})

    async def create(self, data: Document) -> Document:
        result = await self.collection.insert_one(data)
        return {**data, "_id": result.inserted_id}

    async def update(self, outfit_id: ObjectId, changes: Document) -> Document | None:
        return await self.collection.find_one_and_update(
            {"_id": outfit_id}, {"$set": changes}, return_document=ReturnDocument.AFTER
        )

    async def delete(self, outfit_id: ObjectId) -> Document | None:
        return await self.collection.find_one_and_delete({"_id": outfit_id})

    async def save_photo(self, filename: str, data: bytes) -> ObjectId:
        return await self.photos.save(filename, data)

    async def read_photo(self, file_id: ObjectId) -> bytes | None:
        return await self.photos.read(file_id)

    async def delete_photo(self, file_id: ObjectId) -> None:
        await self.photos.delete(file_id)
