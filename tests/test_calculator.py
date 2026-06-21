"""
Tests for Layer 2 (calculator.py).

These exist so that when you (or a recruiter skimming your repo) ask
"does the math actually work", the answer is "yes, here's the proof"
instead of "trust me".
"""

from backend.calculator import calculate_footprint
from backend.schemas import DietInput, EnergyInput, TransportInput, UserLifestyleInput


def _sample_input(**overrides):
    defaults = dict(
        transport=TransportInput(mode="car_petrol", weekly_distance_km=100),
        energy=EnergyInput(monthly_electricity_kwh=200, cooking_fuel="lpg"),
        diet=DietInput(diet_type="non_vegetarian_moderate"),
    )
    defaults.update(overrides)
    return UserLifestyleInput(**defaults)


def test_breakdown_percentages_sum_to_roughly_100():
    result = calculate_footprint(_sample_input())
    total_percentage = sum(b.percentage_of_total for b in result.breakdown)
    assert 99.0 <= total_percentage <= 101.0  # rounding tolerance


def test_walk_or_cycle_has_zero_transport_emissions():
    result = calculate_footprint(
        _sample_input(transport=TransportInput(mode="walk_or_cycle", weekly_distance_km=50))
    )
    transport_breakdown = next(b for b in result.breakdown if b.category == "transport")
    assert transport_breakdown.kg_co2_per_month == 0.0


def test_more_distance_means_more_emissions():
    low = calculate_footprint(
        _sample_input(transport=TransportInput(mode="car_petrol", weekly_distance_km=20))
    )
    high = calculate_footprint(
        _sample_input(transport=TransportInput(mode="car_petrol", weekly_distance_km=200))
    )
    assert high.total_kg_co2_per_month > low.total_kg_co2_per_month


def test_dominant_category_is_the_largest_contributor():
    result = calculate_footprint(_sample_input())
    dominant_breakdown = next(
        b for b in result.breakdown if b.category == result.dominant_category
    )
    other_values = [
        b.kg_co2_per_month for b in result.breakdown if b.category != result.dominant_category
    ]
    assert all(dominant_breakdown.kg_co2_per_month >= v for v in other_values)


def test_vegan_diet_produces_less_co2_than_heavy_meat_diet():
    vegan = calculate_footprint(_sample_input(diet=DietInput(diet_type="vegan")))
    heavy_meat = calculate_footprint(
        _sample_input(diet=DietInput(diet_type="non_vegetarian_heavy"))
    )
    assert vegan.total_kg_co2_per_month < heavy_meat.total_kg_co2_per_month