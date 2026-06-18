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


def _energy_kg_per_month(data: UserLifestyleInput) -> float:
    electricity = data.energy.monthly_electricity_kwh * INDIA_GRID_EMISSION_FACTOR_KG_PER_KWH
    cooking = COOKING_FUEL_KG_CO2_PER_MONTH[data.energy.cooking_fuel]
    return electricity + cooking


def _diet_kg_per_month(data: UserLifestyleInput) -> float:
    return DIET_KG_CO2_PER_DAY[data.diet.diet_type] * DAYS_PER_MONTH


def calculate_footprint(data: UserLifestyleInput) -> FootprintResult:
    """
    The single entry point Layer 1 (or any future input source, like
    an OCR'd bill) should call. Give it a UserLifestyleInput, get back
    a fully-formed FootprintResult.
    """

    transport_kg = round(_transport_kg_per_month(data), 1)
    energy_kg = round(_energy_kg_per_month(data), 1)
    diet_kg = round(_diet_kg_per_month(data), 1)

    total_kg = round(transport_kg + energy_kg + diet_kg, 1)

    raw = {
        "transport": transport_kg,
        "energy": energy_kg,
        "diet": diet_kg,
    }

    breakdown = [
        CategoryBreakdown(
            category=category,
            kg_co2_per_month=kg,
            percentage_of_total=round((kg / total_kg) * 100, 1) if total_kg else 0.0,
        )
        for category, kg in raw.items()
    ]

    dominant_category = max(raw, key=raw.get)

    return FootprintResult(
        total_kg_co2_per_month=total_kg,
        breakdown=breakdown,
        dominant_category=dominant_category,
    )