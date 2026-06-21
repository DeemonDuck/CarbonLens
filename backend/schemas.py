"""
Layer 1 - Input Collection Schema
----------------------------------
This is the contract between "what a human typed into a form" and
"what the rest of the system is allowed to receive."

Why this matters: Layer 2 (emission calculation) will trust this data
completely - no re-checking, no guessing types. If a value is wrong
or missing, Pydantic raises an error HERE, before it ever reaches the
math. That's the whole point of having a dedicated input layer instead
of just reading raw form values everywhere.

Each lifestyle category (transport, energy, diet) is its own class so
we can add new categories later (shopping, digital footprint, etc.)
without touching the existing ones.
"""

from typing import Literal

from pydantic import BaseModel, Field


class TransportInput(BaseModel):
    """How the user mostly gets around, on average."""

    mode: Literal[
        "car_petrol",
        "car_diesel",
        "car_electric",
        "two_wheeler",
        "public_transport",
        "walk_or_cycle",
    ]
    weekly_distance_km: float = Field(
        ..., ge=0, description="Total distance covered per week, in km"
    )


class EnergyInput(BaseModel):
    """Household energy usage - electricity + cooking fuel."""

    monthly_electricity_kwh: float = Field(
        ..., ge=0, description="Monthly electricity usage in kWh (check your bill)"
    )
    cooking_fuel: Literal[
        "lpg",
        "piped_natural_gas",
        "electric",
        "firewood",
    ]


class DietInput(BaseModel):
    """Diet pattern - one of the biggest hidden contributors to footprint."""

    diet_type: Literal[
        "vegan",
        "vegetarian",
        "eggetarian",
        "non_vegetarian_moderate",
        "non_vegetarian_heavy",
    ]


class UserLifestyleInput(BaseModel):
    """
    The full Layer 1 payload.

    This is the single object that gets handed off to Layer 2.
    Nothing downstream should ever need to know HOW this data was
    collected (form, API call, OCR'd bill, etc.) - only that it
    matches this shape.
    """

    transport: TransportInput
    energy: EnergyInput
    diet: DietInput


# ---------------------------------------------------------------------
# Output-side schemas (filled in by Layer 2 - calculator.py)
# ---------------------------------------------------------------------

class CategoryBreakdown(BaseModel):
    """How much one category (transport/energy/diet) contributed."""

    category: Literal["transport", "energy", "diet"]
    kg_co2_per_month: float
    percentage_of_total: float


class FootprintResult(BaseModel):
    """
    The complete output of Layer 2.

    Layer 3 (awareness.py) and Layer 4 (recommendations.py) both
    consume this object - neither of them needs to know anything
    about emission factors or how the math was done.
    """

    total_kg_co2_per_month: float
    breakdown: list[CategoryBreakdown]
    dominant_category: Literal["transport", "energy", "diet"]


class StoryCard(BaseModel):
    """
    The complete output of Layer 3 (awareness.py).

    A typed model instead of a raw dict means a typo in a field name
    fails immediately at construction time, not silently when the UI
    tries to render a missing key.
    """

    headline: str
    narrative: str
    dominant_category: Literal["transport", "energy", "diet"]
    dominant_percentage: float
    equivalents: list[str]


# ---------------------------------------------------------------------
# Human-readable labels for each input option.
#
# This is the single source of truth for "what a user sees" vs "what
# the system stores." Previously the frontend kept its own hardcoded
# copy of these mappings, which meant adding a new transport mode
# required updating two files by hand and risked them drifting out of
# sync. Now there's exactly one place to update.
# ---------------------------------------------------------------------

TRANSPORT_MODE_LABELS: dict[str, str] = {
    "car_petrol": "Petrol car",
    "car_diesel": "Diesel car",
    "car_electric": "Electric car",
    "two_wheeler": "Two-wheeler (bike/scooter)",
    "public_transport": "Public transport (bus/metro/train)",
    "walk_or_cycle": "Mostly walk or cycle",
}

COOKING_FUEL_LABELS: dict[str, str] = {
    "lpg": "LPG cylinder",
    "piped_natural_gas": "Piped natural gas (PNG)",
    "electric": "Electric stove/induction",
    "firewood": "Firewood",
}

DIET_TYPE_LABELS: dict[str, str] = {
    "vegan": "Vegan",
    "vegetarian": "Vegetarian",
    "eggetarian": "Eggetarian",
    "non_vegetarian_moderate": "Non-vegetarian (moderate, few times a week)",
    "non_vegetarian_heavy": "Non-vegetarian (daily/heavy)",
}