from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    mongodb_url: str = "mongodb://localhost:27018"
    mongodb_db: str = "lifetracker"
    cors_origins: list[str] = ["http://localhost:3000"]

    # TMDB (movie details). A v3 API key or a v4 API Read Access Token. Empty = details off.
    tmdb_api_key: str = ""

    # Open Food Facts asks apps to identify themselves; no personal contact details are sent.
    food_database_user_agent: str = "LifeTracker/0.1 (personal app)"
    # Open Food Facts allows 10 searches per minute per IP.
    food_database_searches_per_minute: int = 10


settings = Settings()
