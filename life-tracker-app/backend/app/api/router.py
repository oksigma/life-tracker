from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.calendar.router import router as calendar_router
from app.modules.clothing.router import router as clothing_router
from app.modules.food.router import router as food_router
from app.modules.movies.router import router as movies_router

api_router = APIRouter(prefix="/api")


@api_router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(auth_router)
api_router.include_router(movies_router)
api_router.include_router(clothing_router)
api_router.include_router(food_router)
api_router.include_router(calendar_router)
