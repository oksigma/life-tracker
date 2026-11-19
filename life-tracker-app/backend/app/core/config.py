from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    mongodb_url: str = "mongodb://localhost:27018"
    mongodb_db: str = "lifetracker"
    cors_origins: list[str] = ["http://localhost:3000"]

    # TMDB (movie details). A v3 API key or a v4 API Read Access Token. Empty = details off.
    tmdb_api_key: str = ""

    # App password (spec 0006). Empty = no login (local development).
    app_password: str = ""
    # Extra secret mixed into the session-cookie signing key. Set a long random value when deployed.
    session_secret: str = ""
    session_days: int = 90
    # Send the session cookie only over https. Turn off only for testing a password over plain http.
    session_cookie_secure: bool = True

    # Open Food Facts asks apps to identify themselves; no personal contact details are sent.
    food_database_user_agent: str = "LifeTracker/0.1 (personal app)"
    # Open Food Facts allows 10 searches per minute per IP.
    food_database_searches_per_minute: int = 10


settings = Settings()
