from datetime import date, datetime
from typing import Annotated, Self

from pydantic import BaseModel, StringConstraints, field_validator, model_validator

from app.core.time import validate_not_future

Notes = Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)]


def _empty_to_none(value: str | None) -> str | None:
    return value or None


class OutfitCreateForm(BaseModel):
    """Form fields sent alongside the photo upload."""

    worn_on: date | None = None
    notes: Notes | None = None

    _check_worn_on = field_validator("worn_on")(validate_not_future)
    _clean_notes = field_validator("notes")(_empty_to_none)


class OutfitUpdate(BaseModel):
    worn_on: date | None = None
    notes: Notes | None = None

    _check_worn_on = field_validator("worn_on")(validate_not_future)
    _clean_notes = field_validator("notes")(_empty_to_none)

    @model_validator(mode="after")
    def worn_on_not_null(self) -> Self:
        if "worn_on" in self.model_fields_set and self.worn_on is None:
            raise ValueError("worn_on cannot be null")
        return self


class Outfit(BaseModel):
    id: str
    worn_on: date
    notes: str | None
    photo_url: str
    thumbnail_url: str
    created_at: datetime
    updated_at: datetime


class OutfitList(BaseModel):
    items: list[Outfit]
    total: int
