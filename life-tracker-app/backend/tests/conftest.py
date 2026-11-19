import os
from collections.abc import Iterator

import pytest

# Use a separate database for tests. Must be set before the app (and its settings) is imported.
os.environ["MONGODB_DB"] = "lifetracker_test"
# Never call the real TMDB from tests (it is faked where needed), even if .env has a key.
os.environ["TMDB_API_KEY"] = ""

from fastapi.testclient import TestClient  # noqa: E402
from pymongo import MongoClient  # noqa: E402
from pymongo.database import Database  # noqa: E402
from pymongo.errors import PyMongoError  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def mongo() -> Iterator[MongoClient]:
    sync_client: MongoClient = MongoClient(settings.mongodb_url, serverSelectionTimeoutMS=1500)
    try:
        sync_client.admin.command("ping")
    except PyMongoError:
        pytest.skip(f"MongoDB not reachable at {settings.mongodb_url}; run `npm run db:up`")
    sync_client.drop_database(settings.mongodb_db)
    try:
        yield sync_client
    finally:
        sync_client.drop_database(settings.mongodb_db)
        sync_client.close()


@pytest.fixture
def db(mongo: MongoClient) -> Database:
    """Direct (sync) access to the test database, for checking what was stored."""
    return mongo[settings.mongodb_db]


@pytest.fixture
def client(mongo: MongoClient) -> Iterator[TestClient]:
    """A test client backed by a fresh, empty test database. Needs MongoDB (`npm run db:up`)."""
    with TestClient(app) as test_client:
        yield test_client
