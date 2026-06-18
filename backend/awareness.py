"""
Layer 3 - Awareness Translator
----------------------------------
A number like "437 kg CO2/month" means nothing to most people on its
own. This layer's only job is translation: turn that number into
things people already have an intuition for (a road trip, a tree,
a phone charge), then stitch it into a short story instead of a
spreadsheet row.

This is deliberately separate from calculator.py - the math is
authoritative and rarely changes, but HOW we explain it is something
you'll want to keep tweaking and experimenting with.
"""

from backend.schemas import FootprintResult

# ---------------------------------------------------------------------
# Comparison reference points (approximate, commonly cited figures -
# precise enough for "does this feel big or small", not for an audit).
# ---------------------------------------------------------------------
TREE_ABSORPTION_KG_CO2_PER_YEAR = 21.0       # one mature tree, per year
DELHI_JAIPUR_ONE_WAY_KM = 280.0
AVG_PETROL_CAR_KG_CO2_PER_KM = 0.18
SMARTPHONE_CHARGE_KG_CO2 = 0.008             # one full charge, ~8g

CATEGORY_LABELS = {
    "transport": "Transport",
    "energy": "Energy (electricity + cooking)",
    "diet": "Diet",
}


def build_equivalents(result: FootprintResult) -> list[str]:
    """A handful of relatable comparisons for the total monthly footprint."""
 
    total = result.total_kg_co2_per_month
 
    km_equivalent = total / AVG_PETROL_CAR_KG_CO2_PER_KM
    trips_equivalent = km_equivalent / (DELHI_JAIPUR_ONE_WAY_KM * 2)  # round trips
    tree_years_equivalent = total / TREE_ABSORPTION_KG_CO2_PER_YEAR
    charges_equivalent = total / SMARTPHONE_CHARGE_KG_CO2
 
    return [
        f"Like driving an average petrol car for {km_equivalent:,.0f} km "
        f"— roughly {trips_equivalent:.1f} Delhi–Jaipur round trips.",
        f"It would take about {tree_years_equivalent:.1f} tree-years "
        f"(one tree, growing for that many years) to soak this back up.",
        f"Equivalent to charging a smartphone {charges_equivalent:,.0f} times.",
    ]


def build_story(result: FootprintResult) -> dict:
    """
    Assembles the full 'AI Awareness Card' content: a headline, a short
    narrative paragraph, and the supporting equivalents - everything
    the frontend needs to render the story instead of a bare number.
    """
 
    dominant_label = CATEGORY_LABELS[result.dominant_category]
    dominant_breakdown = next(
        b for b in result.breakdown if b.category == result.dominant_category
    )
 
    headline = f"You generated {result.total_kg_co2_per_month:,.0f} kg CO₂ this month."
 
    narrative = (
        f"That's not one big decision - it's the sum of small, everyday ones. "
        f"{dominant_label} is doing most of the damage here, contributing "
        f"{dominant_breakdown.percentage_of_total:.0f}% of your total. "
        f"Nobody's asking you to overhaul your life overnight - but knowing "
        f"where the weight is sitting is the first real step."
    )
 
    return {
        "headline": headline,
        "narrative": narrative,
        "dominant_category": result.dominant_category,
        "dominant_percentage": dominant_breakdown.percentage_of_total,
        "equivalents": build_equivalents(result),
    }
 