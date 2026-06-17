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

from pydantic import BaseModel, Field
from typing import Literal


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
