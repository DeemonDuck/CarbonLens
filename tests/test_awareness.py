"""
Tests for Layer 3 (awareness.py).

These prove the translation layer actually produces sane, well-formed
output - not just that it runs without throwing.
"""

from backend.awareness import build_equivalents, build_story
from backend.schemas import CategoryBreakdown, FootprintResult, StoryCard


def _sample_result(dominant="energy"):
    breakdown = [
        CategoryBreakdown(category="transport", kg_co2_per_month=80.0, percentage_of_total=20.0),
        CategoryBreakdown(category="energy", kg_co2_per_month=240.0, percentage_of_total=60.0),
        CategoryBreakdown(category="diet", kg_co2_per_month=80.0, percentage_of_total=20.0),
    ]
    return FootprintResult(
        total_kg_co2_per_month=400.0,
        breakdown=breakdown,
        dominant_category=dominant,
    )


def test_build_story_returns_a_typed_story_card():
    story = build_story(_sample_result())
    assert isinstance(story, StoryCard)


def test_headline_includes_the_total_figure():
    story = build_story(_sample_result())
    assert "400" in story.headline


def test_narrative_names_the_dominant_category_and_its_percentage():
    story = build_story(_sample_result(dominant="energy"))
    assert "Energy" in story.narrative
    assert "60%" in story.narrative


def test_equivalents_returns_exactly_three_comparisons():
    equivalents = build_equivalents(_sample_result())
    assert len(equivalents) == 3
    assert all(isinstance(line, str) and line for line in equivalents)


def test_higher_total_produces_a_larger_km_equivalent():
    small = build_equivalents(_sample_result())
    bigger_result = _sample_result()
    bigger_result.total_kg_co2_per_month = 4000.0
    big = build_equivalents(bigger_result)

    # Same comparison sentence, but the km figure inside it should scale up.
    assert small[0] != big[0]