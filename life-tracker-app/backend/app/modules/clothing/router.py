from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    Response,
    UploadFile,
    status,
)
from pymongo.asynchronous.database import AsyncDatabase

from app.core.images import InvalidImageError
from app.core.uploads import PHOTO_CACHE_HEADERS, read_photo_upload, unsupported_photo_error
from app.db.mongo import get_db
from app.modules.clothing.repository import OutfitRepository
from app.modules.clothing.schemas import Outfit, OutfitCreateForm, OutfitList, OutfitUpdate
from app.modules.clothing.service import OutfitService, PhotoSize

router = APIRouter(prefix="/clothing", tags=["clothing"])


def get_service(db: Annotated[AsyncDatabase, Depends(get_db)]) -> OutfitService:
    return OutfitService(OutfitRepository(db))


ServiceDep = Annotated[OutfitService, Depends(get_service)]


@router.get("/outfits")
async def list_outfits(
    service: ServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 60,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> OutfitList:
    return await service.list(limit, offset)


@router.post("/outfits", status_code=status.HTTP_201_CREATED)
async def create_outfit(
    service: ServiceDep,
    photo: Annotated[UploadFile, File(description="JPEG, PNG, WebP or HEIC, up to 15 MB")],
    form: Annotated[OutfitCreateForm, Form()],
) -> Outfit:
    data = await read_photo_upload(photo)
    try:
        return await service.create(data, form)
    except InvalidImageError:
        raise unsupported_photo_error() from None


@router.get("/outfits/{outfit_id}")
async def get_outfit(service: ServiceDep, outfit_id: str) -> Outfit:
    return await service.get(outfit_id)


@router.patch("/outfits/{outfit_id}")
async def update_outfit(service: ServiceDep, outfit_id: str, payload: OutfitUpdate) -> Outfit:
    return await service.update(outfit_id, payload)


@router.delete("/outfits/{outfit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_outfit(service: ServiceDep, outfit_id: str) -> Response:
    await service.delete(outfit_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _photo_response(service: OutfitService, outfit_id: str, size: PhotoSize) -> Response:
    data = await service.read_photo(outfit_id, size)
    return Response(content=data, media_type="image/jpeg", headers=PHOTO_CACHE_HEADERS)


@router.get("/outfits/{outfit_id}/photo", response_class=Response)
async def get_outfit_photo(service: ServiceDep, outfit_id: str) -> Response:
    return await _photo_response(service, outfit_id, "photo")


@router.get("/outfits/{outfit_id}/thumbnail", response_class=Response)
async def get_outfit_thumbnail(service: ServiceDep, outfit_id: str) -> Response:
    return await _photo_response(service, outfit_id, "thumbnail")
