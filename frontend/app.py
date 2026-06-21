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

Accessibility notes
-------------------
Every interactive widget carries:
  - A descriptive visible label (not relying on placeholder text alone)
  - label_visibility="visible" set explicitly so screen-readers
    see the label even if we later move to a collapsed layout
  - A help= tooltip that explains *why* we're asking, not just *what*
  - A stable key= so Streamlit's accessibility tree stays consistent
    across reruns (avoids anonymous widget IDs)
  - st.caption() context before each section so users understand
    what the group of questions is measuring

The theme (config.toml) sets a foreground/background pair that meets
the WCAG 2.1 AA contrast ratio of ≥ 4.5:1 for normal text.
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

# Page config — title and icon appear in the browser tab and are read
# by assistive technologies as the document title.
st.set_page_config(
    page_title="CarbonLens — Estimate your monthly carbon footprint",
    page_icon="🌍",
    layout="centered",
)

st.title("🌍 What's your carbon footprint?")
st.caption(
    "No daily tracking, no guilt-tripping — answer once, see where you "
    "stand, and only dig into 'how to reduce it' if you're curious."
)

st.divider()

# ---------------------------------------------------------------------
# Layer 1 - collect inputs
# Accessibility: each section opens with a st.caption() that explains
# what the group measures and why, so users understand the purpose
# before they encounter the individual inputs.
# ---------------------------------------------------------------------

# --- Transport ---
st.subheader("🚗 Transport")
st.caption(
    "Transport is often the single largest contributor to a personal "
    "carbon footprint. Pick the mode you rely on most, then estimate "
    "your total weekly distance — commutes, errands, everything."
)

# Reverse the canonical {code: label} mapping so the selectbox can show
# labels while we still store the underlying code - codes/labels live
# in exactly one place (schemas.py), not duplicated here.
transport_code_by_label = {label: code for code, label in TRANSPORT_MODE_LABELS.items()}
transport_choice = st.selectbox(
    "How do you mostly travel?",
    options=list(TRANSPORT_MODE_LABELS.values()),
    help=(
        "Choose whichever mode covers the majority of your weekly travel. "
        "If you use multiple modes, pick the one with the most km."
    ),
    label_visibility="visible",
    key="transport_mode_select",
)
weekly_distance_km = st.number_input(
    "Roughly how many km do you cover per week (all trips combined)?",
    min_value=0.0,
    step=5.0,
    value=50.0,
    help=(
        "Add up all your trips for a typical week — daily commute, "
        "errands, weekend outings. An approximate figure is fine; "
        "this isn't a precise log."
    ),
    label_visibility="visible",
    key="weekly_distance_km_input",
)

# --- Energy ---
st.subheader("⚡ Energy")
st.caption(
    "Household energy — electricity and cooking fuel — is the second "
    "major lever. Your electricity bill lists your monthly units consumed "
    "(kWh); use that figure directly."
)

monthly_electricity_kwh = st.number_input(
    "Monthly electricity usage in kWh (check your electricity bill)",
    min_value=0.0,
    step=10.0,
    value=150.0,
    help=(
        "Look for 'units consumed' on your most recent electricity bill. "
        "For India, one unit = 1 kWh. A typical urban household uses "
        "100–300 kWh per month."
    ),
    label_visibility="visible",
    key="monthly_electricity_kwh_input",
)
fuel_code_by_label = {label: code for code, label in COOKING_FUEL_LABELS.items()}
fuel_choice = st.selectbox(
    "What do you mostly cook with?",
    options=list(COOKING_FUEL_LABELS.values()),
    help=(
        "Select your primary cooking fuel. If you use both LPG and an "
        "electric induction top, pick whichever you use more. Electric "
        "cooking energy is already captured in your kWh figure above."
    ),
    label_visibility="visible",
    key="cooking_fuel_select",
)

# --- Diet ---
st.subheader("🍽️ Diet")
st.caption(
    "Diet is a hidden but significant contributor — food production "
    "generates emissions even before it reaches your plate. Pick the "
    "pattern that best describes a normal week for you."
)

diet_code_by_label = {label: code for code, label in DIET_TYPE_LABELS.items()}
diet_choice = st.selectbox(
    "Which best describes your diet?",
    options=list(DIET_TYPE_LABELS.values()),
    help=(
        "This is about typical patterns, not perfection. 'Moderate "
        "non-vegetarian' means meat a few times a week; 'heavy' means "
        "daily. Pick the closest fit — there's no wrong answer."
    ),
    label_visibility="visible",
    key="diet_type_select",
)

st.divider()

# ---------------------------------------------------------------------
# Layers 2 + 3 - calculate, then tell the story
# ---------------------------------------------------------------------
if st.button(
    "See my footprint ➜",
    type="primary",
    key="calculate_footprint_btn",
    help="Calculate your estimated monthly carbon footprint based on the inputs above.",
):
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

    except ValueError as e:
        st.error(
            f"One of your inputs is outside the expected range: {e}. "
            "Please check that distance and electricity values are non-negative."
        )
    except KeyError as e:
        st.error(
            f"An unrecognised option was selected ({e}). "
            "Please reload the page and try again."
        )
    except Exception as e:
        st.error(
            f"Something went wrong while calculating your footprint: {e}. "
            "If this persists, please reload the page."
        )

# ---------------------------------------------------------------------
# Render the AI Awareness Card if we have a result
# Accessibility: st.metric is announced as a labelled value by screen
# readers; column layout is avoided for the breakdown so each line
# appears in document order without needing visual scanning.
# ---------------------------------------------------------------------
if "result" in st.session_state:
    result = st.session_state["result"]
    story = st.session_state["story"]

    # Primary result — metric widget has a label read by assistive tech
    st.metric(
        label="Estimated monthly carbon footprint",
        value=f"{result.total_kg_co2_per_month:,.0f} kg CO₂/month",
    )

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

    # The reduction tips button is intentionally not shown automatically —
    # it only appears after a result exists, and only runs when clicked.
    # This respects the app's core philosophy: curiosity-driven, not pushed.
    if st.button(
        "How can I reduce this? 🌱",
        key="get_recommendations_btn",
        help=(
            "Get personalised, evidence-based suggestions for reducing "
            "your footprint — tailored to your biggest contributor."
        ),
    ):
        with st.spinner("Putting together a few ideas..."):
            tips = generate_recommendations(result, st.session_state["lifestyle"])
        st.markdown("**A few places to start:**")
        for tip in tips:
            st.write(f"- {tip}")
