"""
Emission Factors - the raw numbers everything else is built on
-------------------------------------------------------------------
These are reference constants, not invented numbers. Sources are noted
next to each block so you can defend every figure if a judge asks
"where did this come from?" - and so you can swap in more precise
numbers later without touching calculator.py at all.

If you want to push accuracy further later: replace these with
region-specific datasets (e.g. state-wise DISCOM grid factors instead
of one national average).
"""

# ---------------------------------------------------------------------
# Electricity - Source: Central Electricity Authority (CEA),
# CO2 Baseline Database for the Indian Power Sector, v20.0 (2024).
# National weighted-average grid emission factor.
# ---------------------------------------------------------------------
INDIA_GRID_EMISSION_FACTOR_KG_PER_KWH = 0.71

# ---------------------------------------------------------------------
# Transport - kg CO2 per km, per traveller.
# Sources: UK DEFRA/NHS conversion factors (car/bus averages), adapted
# for typical Indian fleet composition (smaller engine sizes than
# UK/EU averages -> figures trimmed down accordingly), plus ICCT data
# on Indian 2-wheeler lifecycle emissions. EV figure is derived from
# the grid factor above, not a separate published constant.
# ---------------------------------------------------------------------
TRANSPORT_EMISSION_FACTORS_KG_PER_KM = {
    "car_petrol": 0.18,
    "car_diesel": 0.19,
    # EV "tailpipe" emissions are zero, but charging isn't free -
    # ~0.15 kWh consumed per km, multiplied by the grid factor above.
    "car_electric": round(0.15 * INDIA_GRID_EMISSION_FACTOR_KG_PER_KWH, 3),
    "two_wheeler": 0.05,
    "public_transport": 0.10,
    "walk_or_cycle": 0.0,
}

# ---------------------------------------------------------------------
# Cooking fuel - flat kg CO2 per month, assuming typical household
# consumption levels (one ~14.2kg LPG cylinder/month is a common
# Indian household average).
# Source: LPG combustion factor (2.983 kg CO2/kg) from the GHG
# Protocol's emission factor tool; PNG/firewood figures are
# approximated relative to LPG for a comparable energy outpu.
# Electric cooking is intentionally left at 0 here - that energy use
# is already captured in monthly_electricity_kwh, so adding it again
# here would double-count it.
# ---------------------------------------------------------------------
COOKING_FUEL_KG_CO2_PER_MONTH = {
    "lpg": round(14.2 * 2.983, 1),       # ~42.4 kg/month
    "piped_natural_gas": 35.0,
    "electric": 0.0,                      # already counted via electricity
    "firewood": 20.0,
}

# ---------------------------------------------------------------------
# Diet - kg CO2-equivalent per day, averaged across multiple published
# diet-footprint studies (e.g. Shrink That Footprint's diet comparison,
# Scarborough et al.'s UK dietary GHG study). These are directional
# averages, not lab-measured values for any single person's plate -
# treat them as "which bucket is heavier", not a precise count.
# ---------------------------------------------------------------------
DIET_KG_CO2_PER_DAY = {
    "vegan": 1.5,
    "vegetarian": 1.7,
    "eggetarian": 2.0,
    "non_vegetarian_moderate": 2.5,
    "non_vegetarian_heavy": 3.3,
}

# Used to convert weekly figures collected in Layer 1 into monthly ones.
WEEKS_PER_MONTH = 4.345
DAYS_PER_MONTH = 30