from fastapi import Request
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import settings


def create_client() -> AsyncMongoClient:
    return AsyncMongoClient(settings.mongodb_url, tz_aware=True)


def get_db(request: Request) -> AsyncDatabase:
    """FastAPI dependency: the database opened in the app's lifespan."""
    return request.app.state.db
