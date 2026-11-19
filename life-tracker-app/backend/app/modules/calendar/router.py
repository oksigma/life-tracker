from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.asynchronous.database import AsyncDatabase

from app.db.mongo import get_db
from app.modules.calendar.schemas import MAX_RANGE_DAYS, CalendarRange, DayEntries
from app.modules.calendar.service import CalendarService
from app.modules.clothing.repository import OutfitRepository
from app.modules.clothing.service import OutfitService
from app.modules.food.repository import MealRepository, SavedFoodRepository
from app.modules.food.service import MealService
from app.modules.movies.repository import MovieRepository
from app.modules.movies.service import MovieService

router = APIRouter(prefix="/calendar", tags=["calendar"])


def get_service(db: Annotated[AsyncDatabase, Depends(get_db)]) -> CalendarService:
    return CalendarService(
        movies=MovieService(MovieRepository(db)),
        clothing=OutfitService(OutfitRepository(db)),
        food=MealService(MealRepository(db), SavedFoodRepository(db)),
    )


ServiceDep = Annotated[CalendarService, Depends(get_service)]


@router.get("")
async def get_range(
    service: ServiceDep,
    start: Annotated[date, Query(description="First day, YYYY-MM-DD")],
    end: Annotated[date, Query(description="Last day (inclusive), YYYY-MM-DD")],
) -> CalendarRange:
    if end < start:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "end must not be before start")
    if (end - start).days + 1 > MAX_RANGE_DAYS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, f"Range must be {MAX_RANGE_DAYS} days or fewer"
        )
    return await service.range(start, end)


@router.get("/days/{day}")
async def get_day(service: ServiceDep, day: date) -> DayEntries:
    return await service.day(day)
