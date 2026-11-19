from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from pymongo.asynchronous.database import AsyncDatabase

from app.core.images import InvalidImageError
from app.core.uploads import PHOTO_CACHE_HEADERS, read_photo_upload, unsupported_photo_error
from app.db.mongo import get_db
from app.modules.food.openfoodfacts import (
    FoodDatabase,
    FoodDatabaseError,
    FoodDatabaseRateLimitedError,
    get_food_database,
)
from app.modules.food.repository import MealRepository, SavedFoodRepository, SearchCacheRepository
from app.modules.food.schemas import (
    FoodLookup,
    Meal,
    MealCreateForm,
    MealList,
    MealUpdate,
    SavedFoodList,
)
from app.modules.food.service import FoodLookupService, MealService, PhotoSize

router = APIRouter(prefix="/food", tags=["food"])


def get_meal_service(db: Annotated[AsyncDatabase, Depends(get_db)]) -> MealService:
    return MealService(MealRepository(db), SavedFoodRepository(db))


def get_lookup_service(
    db: Annotated[AsyncDatabase, Depends(get_db)],
    database: Annotated[FoodDatabase, Depends(get_food_database)],
) -> FoodLookupService:
    return FoodLookupService(database, SearchCacheRepository(db))


MealServiceDep = Annotated[MealService, Depends(get_meal_service)]
LookupServiceDep = Annotated[FoodLookupService, Depends(get_lookup_service)]


@router.get("/meals")
async def list_meals(
    service: MealServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MealList:
    return await service.list(limit, offset)


@router.post("/meals", status_code=status.HTTP_201_CREATED)
async def create_meal(
    service: MealServiceDep,
    form: Annotated[MealCreateForm, Form()],
    photo: Annotated[UploadFile | None, File(description="Optional meal photo")] = None,
) -> Meal:
    data = await read_photo_upload(photo) if photo is not None else None
    try:
        return await service.create(form, data)
    except InvalidImageError:
        raise unsupported_photo_error() from None


@router.get("/meals/{meal_id}")
async def get_meal(service: MealServiceDep, meal_id: str) -> Meal:
    return await service.get(meal_id)


@router.patch("/meals/{meal_id}")
async def update_meal(service: MealServiceDep, meal_id: str, payload: MealUpdate) -> Meal:
    return await service.update(meal_id, payload)


@router.delete("/meals/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal(service: MealServiceDep, meal_id: str) -> Response:
    await service.delete(meal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _photo_response(service: MealService, meal_id: str, size: PhotoSize) -> Response:
    data = await service.read_photo(meal_id, size)
    return Response(content=data, media_type="image/jpeg", headers=PHOTO_CACHE_HEADERS)


@router.get("/meals/{meal_id}/photo", response_class=Response)
async def get_meal_photo(service: MealServiceDep, meal_id: str) -> Response:
    return await _photo_response(service, meal_id, "photo")


@router.get("/meals/{meal_id}/thumbnail", response_class=Response)
async def get_meal_thumbnail(service: MealServiceDep, meal_id: str) -> Response:
    return await _photo_response(service, meal_id, "thumbnail")


@router.get("/foods")
async def search_saved_foods(
    service: MealServiceDep,
    q: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> SavedFoodList:
    return await service.search_saved_foods(q, limit)


@router.get("/lookup")
async def lookup_food(
    service: LookupServiceDep,
    q: Annotated[str, Query(min_length=2, max_length=100, description="Food name to search")],
) -> FoodLookup:
    try:
        return await service.lookup(q)
    except FoodDatabaseRateLimitedError:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "The food database allows 10 searches a minute. Wait a moment, or pick from "
            "My foods or enter the calories yourself.",
        ) from None
    except FoodDatabaseError:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Couldn't reach the food database. Pick from My foods or enter the calories yourself.",
        ) from None
