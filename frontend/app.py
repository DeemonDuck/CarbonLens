"""
Frontend - orchestrates Layers 1 through 4
----------------------------------------------
This file's only job is UI flow. It doesn't know HOW emissions are
calculated, HOW comparisons are built, or HOW tips are generated -
it just calls each layer in order and renders what comes back.
That separation is what lets you swap this for a React frontend
later without rewriting any backend logic.

Flow (matches the diagram):
  User Input -> calculate_footprint() -> total + breakdown
       -> build_story() -> AI Awareness Card
       -> [button click] -> generate_recommendations()
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from backend.schemas import (
    UserLifestyleInput,
    TransportInput,
    EnergyInput,
    DietInput,
    TRANSPORT_MODE_LABELS,
    COOKING_FUEL_LABELS,
    DIET_TYPE_LABELS,
)
from backend.calculator import calculate_footprint
from backend.awareness import build_story
from backend.recommendations import generate_recommendations

st.set_page_config(page_title="Carbon Awareness", page_icon="🌍")

st.title("🌍 What's your carbon footprint?")
st.caption(
    "No daily tracking, no guilt-tripping — answer once, see where you "
    "stand, and only dig into 'how to reduce it' if you're curious."
)

st.divider()

# ---------------------------------------------------------------------
# Layer 1 - collect inputs
# ---------------------------------------------------------------------
st.subheader("🚗 Transport")
# Reverse the canonical {code: label} mapping so the selectbox can show
# labels while we still store the underlying code - codes/labels live
# in exactly one place (schemas.py), not duplicated here.
transport_code_by_label = {label: code for code, label in TRANSPORT_MODE_LABELS.items()}
transport_choice = st.selectbox(
    "How do you mostly travel?",
    list(TRANSPORT_MODE_LABELS.values()),
    help="Whichever mode covers most of your weekly travel.",
)
weekly_distance_km = st.number_input(
    "Roughly how many km do you cover per week (all trips combined)?",
    min_value=0.0, step=5.0, value=50.0,
    help="All trips combined - commute, errands, everything.",
)

st.subheader("⚡ Energy")
monthly_electricity_kwh = st.number_input(
    "Monthly electricity usage in units/kWh (check your electricity bill)",
    min_value=0.0, step=10.0, value=150.0,
    help="Found on your electricity bill, usually labeled 'units consumed.'",
)
fuel_code_by_label = {label: code for code, label in COOKING_FUEL_LABELS.items()}
fuel_choice = st.selectbox(
    "What do you mostly cook with?",
    list(COOKING_FUEL_LABELS.values()),
    help="Your primary cooking fuel, not occasional backups.",
)

st.subheader("🍽️ Diet")
diet_code_by_label = {label: code for code, label in DIET_TYPE_LABELS.items()}
diet_choice = st.selectbox(
    "Which best describes your diet?",
    list(DIET_TYPE_LABELS.values()),
    help="A general pattern, not a precise log - pick the closest fit.",
)

st.divider()

# ---------------------------------------------------------------------
# Layers 2 + 3 - calculate, then tell the story
# ---------------------------------------------------------------------
if st.button("See my footprint ➜", type="primary"):
    try:
        lifestyle = UserLifestyleInput(
            transport=TransportInput(
                mode=transport_code_by_label[transport_choice],
                weekly_distance_km=weekly_distance_km,
            ),
            energy=EnergyInput(
                monthly_electricity_kwh=monthly_electricity_kwh,
                cooking_fuel=fuel_code_by_label[fuel_choice],
            ),
            diet=DietInput(diet_type=diet_code_by_label[diet_choice]),
        )

        result = calculate_footprint(lifestyle)
        story = build_story(result)

        # Stash everything in session_state so the "How can I reduce
        # this?" button below survives the rerun Streamlit triggers
        # on every interaction.
        st.session_state["lifestyle"] = lifestyle
        st.session_state["result"] = result
        st.session_state["story"] = story

    except Exception as e:
        st.error(f"Something didn't validate: {e}")

# ---------------------------------------------------------------------
# Render the AI Awareness Card if we have a result
# ---------------------------------------------------------------------
if "result" in st.session_state:
    result = st.session_state["result"]
    story = st.session_state["story"]

    st.metric("Estimated footprint", f"{result.total_kg_co2_per_month:,.0f} kg CO₂/month")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Where it came from**")
        for b in result.breakdown:
            st.write(f"{b.category.title()}: {b.percentage_of_total:.0f}%")
    with col2:
        st.markdown("**Equivalent to**")
        for line in story.equivalents:
            st.write(f"• {line}")

    st.divider()
    st.markdown("### 🪄 The story behind your number")
    st.write(story.narrative)

    if st.button("How can I reduce this? 🌱"):
        with st.spinner("Putting together a few ideas..."):
            tips = generate_recommendations(result, st.session_state["lifestyle"])
        st.markdown("**A few places to start:**")
        for tip in tips:
            st.write(f"- {tip}")