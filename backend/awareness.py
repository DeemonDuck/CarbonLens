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


