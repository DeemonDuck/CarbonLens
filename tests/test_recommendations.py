"""
Tests for Layer 4 (recommendations.py).

The LLM path is mocked here - these tests never make a real network
call. They prove three things:
  1. The rule-based fallback works when no API key is configured.
  2. A successful LLM response gets parsed into a clean tip list.
  3. Both SDK failures (auth, rate limit, etc.) AND malformed
     responses fall back gracefully instead of crashing the app.
"""

from unittest.mock import MagicMock, patch

from anthropic import AnthropicError

from backend.recommendations import RULE_BASED_TIPS, generate_recommendations
from backend.schemas import (
    CategoryBreakdown,
    DietInput,
    EnergyInput,
    FootprintResult,
    TransportInput,
    UserLifestyleInput,
)


def _sample_result(dominant="transport"):
    breakdown = [
        CategoryBreakdown(category="transport", kg_co2_per_month=300.0, percentage_of_total=70.0),
        CategoryBreakdown(category="energy", kg_co2_per_month=80.0, percentage_of_total=20.0),
        CategoryBreakdown(category="diet", kg_co2_per_month=40.0, percentage_of_total=10.0),
    ]
    return FootprintResult(
        total_kg_co2_per_month=420.0, breakdown=breakdown, dominant_category=dominant
    )


def _sample_lifestyle():
    return UserLifestyleInput(
        transport=TransportInput(mode="car_petrol", weekly_distance_km=150),
        energy=EnergyInput(monthly_electricity_kwh=150, cooking_fuel="lpg"),
        diet=DietInput(diet_type="non_vegetarian_moderate"),
    )


@patch("backend.recommendations.get_anthropic_client")
def test_falls_back_to_rule_based_tips_when_no_client_configured(mock_get_client):
    mock_get_client.return_value = None

    tips = generate_recommendations(_sample_result(dominant="transport"), _sample_lifestyle())

    assert tips == RULE_BASED_TIPS["transport"]


@patch("backend.recommendations.get_anthropic_client")
def test_parses_a_successful_llm_response_into_clean_tips(mock_get_client):
    fake_block = MagicMock()
    fake_block.type = "text"
    fake_block.text = "1. Drive less.\n2. Take the bus.\n3. Carpool twice a week."

    fake_response = MagicMock()
    fake_response.content = [fake_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = fake_response
    mock_get_client.return_value = mock_client

    tips = generate_recommendations(_sample_result(), _sample_lifestyle())

    assert len(tips) == 3
    assert "Drive less" in tips[0]


@patch("backend.recommendations.get_anthropic_client")
def test_falls_back_when_anthropic_sdk_raises(mock_get_client):
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = AnthropicError("rate limited")
    mock_get_client.return_value = mock_client

    tips = generate_recommendations(_sample_result(dominant="diet"), _sample_lifestyle())

    assert tips == RULE_BASED_TIPS["diet"]


@patch("backend.recommendations.get_anthropic_client")
def test_falls_back_when_response_shape_is_unexpected(mock_get_client):
    mock_client = MagicMock()
    # Simulate a malformed/future-SDK response shape - no `.content`
    # attribute at all, which should raise AttributeError when we
    # try to iterate it.
    mock_client.messages.create.return_value = object()
    mock_get_client.return_value = mock_client

    tips = generate_recommendations(_sample_result(dominant="energy"), _sample_lifestyle())

    assert tips == RULE_BASED_TIPS["energy"]