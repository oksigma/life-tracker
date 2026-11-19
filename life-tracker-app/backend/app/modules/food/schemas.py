from datetime import date, datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, Field, Json, StringConstraints, field_validator, model_validator

from app.core.time import validate_not_future

MealType = Literal["breakfast", "lunch", "dinner", "snack"]
Unit = Literal["g", "ml", "serving"]
Source = Literal["openfoodfacts", "manual"]

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Brand = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]
Notes = Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)]

MAX_ITEMS = 50
MAX_ITEM_KCAL = 10_000


def _empty_to_none(value: str | None) -> str | None:
    return value or None


def calculate_kcal(
    quantity: float | None,
    unit: Unit | None,
    kcal_per_100g: float | None,
    kcal_per_serving: float | None,
) -> float | None:
    """Calories for an amount of food, or None if they can't be worked out from the basis given.
    Millilitres are treated like grams (close enough for an estimate)."""
    if quantity is None or unit is None:
        return None
    if unit in ("g", "ml") and kcal_per_100g is not None:
        return kcal_per_100g * quantity / 100
    if unit == "serving" and kcal_per_serving is not None:
        return kcal_per_serving * quantity
    return None


class MealItemIn(BaseModel):
    name: Name
    brand: Brand | None = None
    quantity: Annotated[float, Field(gt=0, le=100_000)] | None = None
    unit: Unit | None = None
    kcal_per_100g: Annotated[float, Field(ge=0, le=1_000)] | None = None
    kcal_per_serving: Annotated[float, Field(ge=0, le=MAX_ITEM_KCAL)] | None = None
    kcal: Annotated[float, Field(ge=0, le=MAX_ITEM_KCAL)] | None = None
    source: Source = "manual"
    off_code: Annotated[str, StringConstraints(max_length=32)] | None = None

    _clean_brand = field_validator("brand")(_empty_to_none)

    @model_validator(mode="after")
    def compute_kcal(self) -> Self:
        if (self.quantity is None) != (self.unit is None):
            raise ValueError("quantity and unit must be given together")
        computed = calculate_kcal(
            self.quantity, self.unit, self.kcal_per_100g, self.kcal_per_serving
        )
        if computed is not None:
            # The backend is the source of truth for calculated calories.
            if computed > MAX_ITEM_KCAL:
                raise ValueError(f"an item can't be more than {MAX_ITEM_KCAL} kcal")
            self.kcal = round(computed, 1)
        elif self.kcal is None:
            raise ValueError("kcal is required when it can't be calculated from the amount")
        return self


class MealItem(MealItemIn):
    kcal: float


Items = Annotated[list[MealItemIn], Field(max_length=MAX_ITEMS)]


class MealCreateForm(BaseModel):
    """Form fields sent alongside the optional photo. `items` is a JSON-encoded list."""

    eaten_on: date | None = None
    meal_type: MealType
    notes: Notes | None = None
    items: Json[Items] = Field(default_factory=list)

    _check_eaten_on = field_validator("eaten_on")(validate_not_future)
    _clean_notes = field_validator("notes")(_empty_to_none)


class MealUpdate(BaseModel):
    eaten_on: date | None = None
    meal_type: MealType | None = None
    notes: Notes | None = None
    items: Items | None = None

    _check_eaten_on = field_validator("eaten_on")(validate_not_future)
    _clean_notes = field_validator("notes")(_empty_to_none)

    @model_validator(mode="after")
    def required_fields_not_null(self) -> Self:
        for name in ("eaten_on", "meal_type", "items"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class Meal(BaseModel):
    id: str
    eaten_on: date
    meal_type: MealType
    notes: str | None
    items: list[MealItem]
    total_kcal: float
    photo_url: str | None
    thumbnail_url: str | None
    created_at: datetime
    updated_at: datetime


class MealList(BaseModel):
    items: list[Meal]
    total: int


class FoodOption(BaseModel):
    """A food that can be added to a meal: from "My foods" or the food database."""

    name: str
    brand: str | None = None
    kcal_per_100g: float | None = None
    kcal_per_serving: float | None = None
    serving_size: str | None = None
    source: Source
    off_code: str | None = None


class SavedFood(FoodOption):
    id: str
    use_count: int


class SavedFoodList(BaseModel):
    items: list[SavedFood]


class FoodLookup(BaseModel):
    results: list[FoodOption]
    cached: bool
