import asyncio
from collections import defaultdict
from datetime import date
from typing import Protocol

from app.modules.calendar.schemas import CalendarDay, CalendarRange, DayEntries
from app.modules.clothing.service import OutfitService
from app.modules.food.service import MealService
from app.modules.movies.service import MovieService


class DayCounter(Protocol):
    async def count_by_day(self, start: date, end: date) -> dict[str, int]: ...


class CalendarService:
    """Combines per-day activity from each life area. To add an area, add its service here
    and a field to `DayEntries`."""

    def __init__(self, movies: MovieService, clothing: OutfitService, food: MealService) -> None:
        self.movies = movies
        self.clothing = clothing
        self.food = food
        self.areas: dict[str, DayCounter] = {"movies": movies, "clothing": clothing, "food": food}

    async def range(self, start: date, end: date) -> CalendarRange:
        results = await asyncio.gather(
            *(area.count_by_day(start, end) for area in self.areas.values())
        )
        counts: dict[str, dict[str, int]] = defaultdict(dict)
        for area, per_day in zip(self.areas, results, strict=True):
            for day, count in per_day.items():
                counts[day][area] = count
        days = [CalendarDay(date=day, counts=counts[day]) for day in sorted(counts)]
        return CalendarRange(start=start, end=end, days=days)

    async def day(self, day: date) -> DayEntries:
        movies, clothing, food = await asyncio.gather(
            self.movies.list_on_day(day), self.clothing.list_on_day(day), self.food.list_on_day(day)
        )
        return DayEntries(date=day, movies=movies, clothing=clothing, food=food)
