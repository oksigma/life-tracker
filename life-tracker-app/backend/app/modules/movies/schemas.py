from datetime import UTC, date, datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

from app.core.time import validate_not_future

WhereWatched = Literal["cinema", "home", "streaming", "other"]

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Notes = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]
Rating = Annotated[int, Field(ge=1, le=5)]

FIRST_FILM_YEAR = 1888


def _validate_year(value: int | None) -> int | None:
    max_year = datetime.now(UTC).year + 1
    if value is not None and not FIRST_FILM_YEAR <= value <= max_year:
        raise ValueError(f"year must be between {FIRST_FILM_YEAR} and {max_year}")
    return value


def _empty_to_none(value: str | None) -> str | None:
    return value or None


class TmdbMatch(BaseModel):
    """A TMDB search result."""

    tmdb_id: int
    title: str
    original_title: str | None = None
    year: int | None = None
    poster_path: str | None = None
    overview: str | None = None


class TmdbSearchResults(BaseModel):
    results: list[TmdbMatch]


class TmdbStatus(BaseModel):
    configured: bool


class MovieDetails(TmdbMatch):
    """Details from TMDB, stored with the movie."""

    release_date: str | None = None
    runtime: int | None = None
    genres: list[str] = []


class AttachDetails(BaseModel):
    """Match a logged movie to TMDB: a specific movie, or the best match for its title."""

    tmdb_id: Annotated[int, Field(ge=1)] | None = None


class MovieCreate(BaseModel):
    title: Title
    watched_on: date
    year: int | None = None
    rating: Rating | None = None
    where: WhereWatched | None = None
    notes: Notes | None = None
    # TMDB movie picked from the suggestions; if missing, the best match for the title is used.
    tmdb_id: Annotated[int, Field(ge=1)] | None = None

    _check_watched_on = field_validator("watched_on")(validate_not_future)
    _check_year = field_validator("year")(_validate_year)
    _clean_notes = field_validator("notes")(_empty_to_none)


class MovieUpdate(BaseModel):
    """PATCH body: any subset of fields. Optional fields can be cleared with null."""

    title: Title | None = None
    watched_on: date | None = None
    year: int | None = None
    rating: Rating | None = None
    where: WhereWatched | None = None
    notes: Notes | None = None

    _check_watched_on = field_validator("watched_on")(validate_not_future)
    _check_year = field_validator("year")(_validate_year)
    _clean_notes = field_validator("notes")(_empty_to_none)

    @model_validator(mode="after")
    def required_fields_not_null(self) -> Self:
        for name in ("title", "watched_on"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class Movie(BaseModel):
    id: str
    title: str
    watched_on: date
    year: int | None
    rating: int | None
    where: WhereWatched | None
    notes: str | None
    details: MovieDetails | None = None
    created_at: datetime
    updated_at: datetime


class MovieList(BaseModel):
    items: list[Movie]
    total: int
