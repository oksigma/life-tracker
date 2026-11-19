# Lazy annotations: the `list` method below would otherwise shadow the builtin in later hints.
from __future__ import annotations

import asyncio
from datetime import date
from typing import Literal

from bson import ObjectId

from app.core.errors import NotFoundError
from app.core.ids import parse_object_id
from app.core.images import process_photo
from app.core.time import utc_now
from app.modules.clothing.repository import Document, OutfitRepository
from app.modules.clothing.schemas import Outfit, OutfitCreateForm, OutfitList, OutfitUpdate

PhotoSize = Literal["photo", "thumbnail"]


def _parse_id(outfit_id: str) -> ObjectId:
    return parse_object_id(outfit_id, "Outfit")


def _to_outfit(doc: Document) -> Outfit:
    outfit_id = str(doc["_id"])
    base = f"/api/clothing/outfits/{outfit_id}"
    return Outfit(
        id=outfit_id,
        worn_on=doc["worn_on"],
        notes=doc.get("notes"),
        photo_url=f"{base}/photo",
        thumbnail_url=f"{base}/thumbnail",
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


class OutfitService:
    def __init__(self, repository: OutfitRepository) -> None:
        self.repository = repository

    async def list(self, limit: int, offset: int) -> OutfitList:
        docs, total = await self.repository.list(limit, offset)
        return OutfitList(items=[_to_outfit(doc) for doc in docs], total=total)

    async def count_by_day(self, start: date, end: date) -> dict[str, int]:
        return await self.repository.count_by_day(start.isoformat(), end.isoformat())

    async def list_on_day(self, day: date) -> list[Outfit]:
        return [_to_outfit(doc) for doc in await self.repository.list_on_day(day.isoformat())]

    async def get(self, outfit_id: str) -> Outfit:
        return _to_outfit(await self._get_doc(outfit_id))

    async def create(self, photo: bytes, form: OutfitCreateForm) -> Outfit:
        processed = await asyncio.to_thread(process_photo, photo)

        worn_on = form.worn_on or date.today()
        photo_id = await self.repository.save_photo(f"{worn_on}.jpg", processed.full)
        thumbnail_id = await self.repository.save_photo(f"{worn_on}-thumb.jpg", processed.thumbnail)
        now = utc_now()
        try:
            doc = await self.repository.create(
                {
                    "worn_on": worn_on.isoformat(),
                    "notes": form.notes,
                    "photo_file_id": photo_id,
                    "thumbnail_file_id": thumbnail_id,
                    "created_at": now,
                    "updated_at": now,
                }
            )
        except Exception:
            # Don't leave orphaned photos behind if the record couldn't be saved.
            await self.repository.delete_photo(photo_id)
            await self.repository.delete_photo(thumbnail_id)
            raise
        return _to_outfit(doc)

    async def update(self, outfit_id: str, payload: OutfitUpdate) -> Outfit:
        object_id = _parse_id(outfit_id)
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            return await self.get(outfit_id)
        if changes.get("worn_on") is not None:
            changes["worn_on"] = changes["worn_on"].isoformat()
        changes["updated_at"] = utc_now()
        doc = await self.repository.update(object_id, changes)
        if doc is None:
            raise NotFoundError("Outfit")
        return _to_outfit(doc)

    async def delete(self, outfit_id: str) -> None:
        doc = await self.repository.delete(_parse_id(outfit_id))
        if doc is None:
            raise NotFoundError("Outfit")
        await self.repository.delete_photo(doc["photo_file_id"])
        await self.repository.delete_photo(doc["thumbnail_file_id"])

    async def read_photo(self, outfit_id: str, size: PhotoSize) -> bytes:
        doc = await self._get_doc(outfit_id)
        file_id = doc["photo_file_id"] if size == "photo" else doc["thumbnail_file_id"]
        data = await self.repository.read_photo(file_id)
        if data is None:
            raise NotFoundError("Photo")
        return data

    async def _get_doc(self, outfit_id: str) -> Document:
        doc = await self.repository.get(_parse_id(outfit_id))
        if doc is None:
            raise NotFoundError("Outfit")
        return doc
