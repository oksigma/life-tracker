from pymongo.asynchronous.database import AsyncDatabase

from app.modules.clothing.repository import OutfitRepository
from app.modules.food.repository import MealRepository, SavedFoodRepository, SearchCacheRepository
from app.modules.movies.repository import MovieRepository


async def ensure_indexes(db: AsyncDatabase) -> None:
    await MovieRepository(db).ensure_indexes()
    await OutfitRepository(db).ensure_indexes()
    await MealRepository(db).ensure_indexes()
    await SavedFoodRepository(db).ensure_indexes()
    await SearchCacheRepository(db).ensure_indexes()
