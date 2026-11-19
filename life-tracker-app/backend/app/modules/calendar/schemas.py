from datetime import date

from pydantic import BaseModel

from app.modules.clothing.schemas import Outfit
from app.modules.food.schemas import Meal
from app.modules.movies.schemas import Movie

MAX_RANGE_DAYS = 366


class CalendarDay(BaseModel):
    date: date
    # Entry counts by life area, e.g. {"movies": 1, "clothing": 2}. Areas with none are left out.
    counts: dict[str, int]


class CalendarRange(BaseModel):
    start: date
    end: date
    days: list[CalendarDay]


class DayEntries(BaseModel):
    date: date
    movies: list[Movie]
    clothing: list[Outfit]
    food: list[Meal]
