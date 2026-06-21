"""
Tests for Layer 2 (calculator.py).

These exist so that when you (or a recruiter skimming your repo) ask
"does the math actually work", the answer is "yes, here's the proof"
instead of "trust me".

Covers:
  - Happy-path arithmetic
  - All transport modes (including zero-emission options)
  - All diet types
  - All cooking fuel types
  - Boundary / edge-case values (zero distance, zero electricity, very high)
  - Dominant-category logic
"""

import pytest

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


# ------------------------------------------------------------------
# Core arithmetic
# ------------------------------------------------------------------

def test_breakdown_percentages_sum_to_roughly_100():
    result = calculate_footprint(_sample_input())
    total_percentage = sum(b.percentage_of_total for b in result.breakdown)
    assert 99.0 <= total_percentage <= 101.0  # rounding tolerance


def test_total_equals_sum_of_breakdown_kg():
    result = calculate_footprint(_sample_input())
    summed = sum(b.kg_co2_per_month for b in result.breakdown)
    assert abs(result.total_kg_co2_per_month - summed) < 0.5  # rounding


def test_more_distance_means_more_emissions():
    low = calculate_footprint(
        _sample_input(transport=TransportInput(mode="car_petrol", weekly_distance_km=20))
    )
    high = calculate_footprint(
        _sample_input(transport=TransportInput(mode="car_petrol", weekly_distance_km=200))
    )
    assert high.total_kg_co2_per_month > low.total_kg_co2_per_month


def test_more_electricity_means_more_emissions():
    low = calculate_footprint(
        _sample_input(energy=EnergyInput(monthly_electricity_kwh=50, cooking_fuel="lpg"))
    )
    high = calculate_footprint(
        _sample_input(energy=EnergyInput(monthly_electricity_kwh=500, cooking_fuel="lpg"))
    )
    assert high.total_kg_co2_per_month > low.total_kg_co2_per_month


def test_dominant_category_is_the_largest_contributor():
    result = calculate_footprint(_sample_input())
    dominant_breakdown = next(
        b for b in result.breakdown if b.category == result.dominant_category
    )
    other_values = [
        b.kg_co2_per_month
        for b in result.breakdown
        if b.category != result.dominant_category
    ]
    assert all(dominant_breakdown.kg_co2_per_month >= v for v in other_values)


# ------------------------------------------------------------------
# Transport modes - one test per mode to ensure no mode is broken
# ------------------------------------------------------------------

@pytest.mark.parametrize("mode", [
    "car_petrol", "car_diesel", "car_electric",
    "two_wheeler", "public_transport",
])
def test_motorised_transport_mode_produces_positive_emissions(mode):
    result = calculate_footprint(
        _sample_input(transport=TransportInput(mode=mode, weekly_distance_km=100))
    )
    transport_breakdown = next(b for b in result.breakdown if b.category == "transport")
    assert transport_breakdown.kg_co2_per_month > 0


def test_walk_or_cycle_has_zero_transport_emissions():
    result = calculate_footprint(
        _sample_input(transport=TransportInput(mode="walk_or_cycle", weekly_distance_km=50))
    )
    transport_breakdown = next(b for b in result.breakdown if b.category == "transport")
    assert transport_breakdown.kg_co2_per_month == 0.0


def test_electric_car_emits_less_than_petrol_car_same_distance():
    petrol = calculate_footprint(
        _sample_input(transport=TransportInput(mode="car_petrol", weekly_distance_km=100))
    )
    electric = calculate_footprint(
        _sample_input(transport=TransportInput(mode="car_electric", weekly_distance_km=100))
    )
    petrol_t = next(b for b in petrol.breakdown if b.category == "transport")
    electric_t = next(b for b in electric.breakdown if b.category == "transport")
    assert electric_t.kg_co2_per_month < petrol_t.kg_co2_per_month


# ------------------------------------------------------------------
# Diet types
# ------------------------------------------------------------------

def test_vegan_diet_produces_less_co2_than_heavy_meat_diet():
    vegan = calculate_footprint(_sample_input(diet=DietInput(diet_type="vegan")))
    heavy_meat = calculate_footprint(
        _sample_input(diet=DietInput(diet_type="non_vegetarian_heavy"))
    )
    assert vegan.total_kg_co2_per_month < heavy_meat.total_kg_co2_per_month


@pytest.mark.parametrize("diet_type,expected_order", [
    ("vegan", 0),
    ("vegetarian", 1),
    ("eggetarian", 2),
    ("non_vegetarian_moderate", 3),
    ("non_vegetarian_heavy", 4),
])
def test_diet_emissions_increase_in_expected_order(diet_type, expected_order):
    """Diet footprint should strictly increase from vegan → heavy meat."""
    diet_types = [
        "vegan", "vegetarian", "eggetarian",
        "non_vegetarian_moderate", "non_vegetarian_heavy",
    ]
    results = [
        calculate_footprint(_sample_input(diet=DietInput(diet_type=dt)))
        for dt in diet_types
    ]
    diet_kgs = [
        next(b.kg_co2_per_month for b in r.breakdown if b.category == "diet")
        for r in results
    ]
    # Each diet should have >= emissions than the one before it
    assert all(diet_kgs[i] <= diet_kgs[i + 1] for i in range(len(diet_kgs) - 1))


# ------------------------------------------------------------------
# Cooking fuel types
# ------------------------------------------------------------------

@pytest.mark.parametrize("fuel", ["lpg", "piped_natural_gas", "electric", "firewood"])
def test_all_cooking_fuels_produce_non_negative_energy_emissions(fuel):
    result = calculate_footprint(
        _sample_input(energy=EnergyInput(monthly_electricity_kwh=0, cooking_fuel=fuel))
    )
    energy_breakdown = next(b for b in result.breakdown if b.category == "energy")
    assert energy_breakdown.kg_co2_per_month >= 0


def test_electric_cooking_fuel_does_not_double_count_electricity():
    """Electric cooking emissions are already in the kWh figure; fuel=electric
    should add 0 on top, unlike lpg which adds ~42 kg."""
    electric_cook = calculate_footprint(
        _sample_input(energy=EnergyInput(monthly_electricity_kwh=100, cooking_fuel="electric"))
    )
    lpg_cook = calculate_footprint(
        _sample_input(energy=EnergyInput(monthly_electricity_kwh=100, cooking_fuel="lpg"))
    )
    assert lpg_cook.total_kg_co2_per_month > electric_cook.total_kg_co2_per_month


# ------------------------------------------------------------------
# Boundary / edge cases
# ------------------------------------------------------------------

def test_zero_distance_produces_zero_transport_emissions():
    result = calculate_footprint(
        _sample_input(transport=TransportInput(mode="car_petrol", weekly_distance_km=0))
    )
    transport_breakdown = next(b for b in result.breakdown if b.category == "transport")
    assert transport_breakdown.kg_co2_per_month == 0.0


def test_zero_electricity_still_produces_cooking_emissions_for_lpg():
    result = calculate_footprint(
        _sample_input(energy=EnergyInput(monthly_electricity_kwh=0, cooking_fuel="lpg"))
    )
    energy_breakdown = next(b for b in result.breakdown if b.category == "energy")
    assert energy_breakdown.kg_co2_per_month > 0


def test_very_high_inputs_produce_very_high_total():
    result = calculate_footprint(
        _sample_input(
            transport=TransportInput(mode="car_petrol", weekly_distance_km=5000),
            energy=EnergyInput(monthly_electricity_kwh=10000, cooking_fuel="lpg"),
        )
    )
    assert result.total_kg_co2_per_month > 10000


def test_all_zero_inputs_still_produce_diet_emissions():
    """Even if transport distance and electricity are zero, diet always contributes."""
    result = calculate_footprint(
        _sample_input(
            transport=TransportInput(mode="walk_or_cycle", weekly_distance_km=0),
            energy=EnergyInput(monthly_electricity_kwh=0, cooking_fuel="electric"),
        )
    )
    assert result.total_kg_co2_per_month > 0


# ------------------------------------------------------------------
# Schema validation (Layer 1 guard)
# ------------------------------------------------------------------

def test_negative_distance_is_rejected_by_schema():
    with pytest.raises(Exception):
        TransportInput(mode="car_petrol", weekly_distance_km=-10)


def test_negative_electricity_is_rejected_by_schema():
    with pytest.raises(Exception):
        EnergyInput(monthly_electricity_kwh=-1, cooking_fuel="lpg")
