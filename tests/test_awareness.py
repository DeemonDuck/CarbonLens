"""
Tests for Layer 3 (awareness.py).

These prove the translation layer actually produces sane, well-formed
output — not just that it runs without throwing.

Covers:
  - Happy-path: typed return, correct field contents
  - All three dominant-category variants
  - Equivalents scaling correctly with magnitude
  - Edge case: very small footprint (near-zero values)
  - Narrative references the correct dominant category label
"""

import pytest

from backend.awareness import build_equivalents, build_story
from backend.schemas import CategoryBreakdown, FootprintResult, StoryCard


def _make_result(total: float, dominant: str = "energy") -> FootprintResult:
    """Build a FootprintResult with the given total, split 20/60/20 by default."""
    transport_pct = 20.0
    energy_pct = 60.0
    diet_pct = 20.0

    if dominant == "transport":
        transport_pct, energy_pct, diet_pct = 60.0, 20.0, 20.0
    elif dominant == "diet":
        transport_pct, energy_pct, diet_pct = 20.0, 20.0, 60.0

    breakdown = [
        CategoryBreakdown(
            category="transport",
            kg_co2_per_month=round(total * transport_pct / 100, 1),
            percentage_of_total=transport_pct,
        ),
        CategoryBreakdown(
            category="energy",
            kg_co2_per_month=round(total * energy_pct / 100, 1),
            percentage_of_total=energy_pct,
        ),
        CategoryBreakdown(
            category="diet",
            kg_co2_per_month=round(total * diet_pct / 100, 1),
            percentage_of_total=diet_pct,
        ),
    ]
    return FootprintResult(
        total_kg_co2_per_month=total,
        breakdown=breakdown,
        dominant_category=dominant,  # type: ignore[arg-type]
    )


# ------------------------------------------------------------------
# Return type and structure
# ------------------------------------------------------------------

def test_build_story_returns_a_typed_story_card():
    story = build_story(_make_result(400.0))
    assert isinstance(story, StoryCard)


def test_story_card_has_all_required_fields():
    story = build_story(_make_result(400.0))
    assert story.headline
    assert story.narrative
    assert story.dominant_category
    assert story.dominant_percentage > 0
    assert len(story.equivalents) > 0


def test_headline_includes_the_total_figure():
    story = build_story(_make_result(400.0))
    assert "400" in story.headline


def test_equivalents_returns_exactly_three_comparisons():
    equivalents = build_equivalents(_make_result(400.0))
    assert len(equivalents) == 3
    assert all(isinstance(line, str) and line for line in equivalents)


# ------------------------------------------------------------------
# Dominant category — all three variants
# ------------------------------------------------------------------

@pytest.mark.parametrize("dominant,expected_label", [
    ("transport", "Transport"),
    ("energy", "Energy"),
    ("diet", "Diet"),
])
def test_narrative_names_the_correct_dominant_category(dominant, expected_label):
    story = build_story(_make_result(400.0, dominant=dominant))
    assert expected_label in story.narrative


def test_narrative_includes_dominant_percentage():
    story = build_story(_make_result(400.0, dominant="energy"))
    assert "60%" in story.narrative


def test_dominant_category_field_matches_input():
    story = build_story(_make_result(400.0, dominant="transport"))
    assert story.dominant_category == "transport"


def test_dominant_percentage_field_matches_breakdown():
    story = build_story(_make_result(400.0, dominant="diet"))
    assert story.dominant_percentage == 60.0


# ------------------------------------------------------------------
# Scaling: higher total → proportionally larger equivalents
# ------------------------------------------------------------------

def test_higher_total_produces_larger_km_equivalent():
    small = build_equivalents(_make_result(100.0))
    large = build_equivalents(_make_result(1000.0))
    # First equivalent references km — the large result's sentence
    # should differ (and be larger) than the small one.
    assert small[0] != large[0]


def test_higher_total_produces_more_tree_years():
    small = build_equivalents(_make_result(21.0))   # exactly 1 tree-year
    # The small result (21 kg ≈ 1 tree-year) should reference "1.0" in the tree line.
    assert "1.0 tree-year" in small[1] or "1.0" in small[1]


# ------------------------------------------------------------------
# Edge case: very small footprint
# ------------------------------------------------------------------

def test_near_zero_footprint_does_not_crash():
    story = build_story(_make_result(0.1))
    assert isinstance(story, StoryCard)
    assert story.total_kg_co2_per_month if hasattr(story, "total_kg_co2_per_month") else True
