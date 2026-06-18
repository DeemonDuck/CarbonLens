"""
Layer 2 - Emission Calculation Engine
----------------------------------------
This is the only file allowed to do carbon math. Everything else
(awareness translations, recommendations, the UI) just consumes the
FootprintResult this produces - they never touch emission_factors.py
directly. That keeps the math centralized and auditable in one place.
"""

from backend.schemas import (
    UserLifestyleInput,
    FootprintResult,
    CategoryBreakdown,
)
from backend.emission_factors import (
    TRANSPORT_EMISSION_FACTORS_KG_PER_KM,
    COOKING_FUEL_KG_CO2_PER_MONTH,
    INDIA_GRID_EMISSION_FACTOR_KG_PER_KWH,
    DIET_KG_CO2_PER_DAY,
    WEEKS_PER_MONTH,
    DAYS_PER_MONTH,
)


def _transport_kg_per_month(data: UserLifestyleInput) -> float:
    factor = TRANSPORT_EMISSION_FACTORS_KG_PER_KM[data.transport.mode]
    monthly_km = data.transport.weekly_distance_km * WEEKS_PER_MONTH
    return monthly_km * factor

