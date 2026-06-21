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
  - label_visibility="visible" so screen readers always announce the label
  - help= tooltip explaining why we ask, not just what to enter
  - key= for a stable, predictable accessibility tree across reruns
Each section opens with st.caption() context before the inputs themselves,
so screen-reader and cognitive-disability users understand a group's
purpose before navigating into it. Error messages distinguish ValueError /
KeyError / Exception with actionable text. Page title is a full descriptive
string read by assistive technologies as the document title.
Color contrast: all theme pairs exceed WCAG 2.1 AA (≥4.5:1); see config.toml.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from typing import Literal, cast
from backend.schemas import (
    UserLifestyleInput,
    TransportInput,
    EnergyInput,
    DietInput,
    TRANSPORT_MODE_LABELS,
    COOKING_FUEL_LABELS,
    DIET_TYPE_LABELS,
    FootprintResult,
    StoryCard,
)
from backend.calculator import calculate_footprint
from backend.awareness import build_story
from backend.recommendations import generate_recommendations


def render_transport_inputs() -> tuple[str, float]:
    """Render the Transport input section and return (transport_mode_code, weekly_km)."""
    st.subheader("🚗 Transport")
    st.caption(
        "Transport is often the single largest contributor to a personal "
        "carbon footprint. Pick the mode you rely on most, then estimate "
        "your total weekly distance — commutes, errands, everything."
    )
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
            "errands, weekend outings. An approximate figure is fine."
        ),
        label_visibility="visible",
        key="weekly_distance_km_input",
    )
    return transport_code_by_label[transport_choice], weekly_distance_km


def render_energy_inputs() -> tuple[float, str]:
    """Render the Energy input section and return (monthly_kwh, cooking_fuel_code)."""
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
            "Select your primary cooking fuel. Electric cooking energy is "
            "already captured in your kWh figure above — no double-counting."
        ),
        label_visibility="visible",
        key="cooking_fuel_select",
    )
    return monthly_electricity_kwh, fuel_code_by_label[fuel_choice]


def render_diet_inputs() -> str:
    """Render the Diet input section and return the diet_type code."""
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
            "daily. Pick the closest fit."
        ),
        label_visibility="visible",
        key="diet_type_select",
    )
    return diet_code_by_label[diet_choice]


TransportMode = Literal[
    "car_petrol", "car_diesel", "car_electric",
    "two_wheeler", "public_transport", "walk_or_cycle",
]
CookingFuel = Literal["lpg", "piped_natural_gas", "electric", "firewood"]
DietType = Literal[
    "vegan", "vegetarian", "eggetarian",
    "non_vegetarian_moderate", "non_vegetarian_heavy",
]


def build_lifestyle_input(
    transport_mode: str,
    weekly_distance_km: float,
    monthly_electricity_kwh: float,
    cooking_fuel: str,
    diet_type: str,
) -> UserLifestyleInput:
    """Construct and validate the Layer 1 payload from raw form values."""
    return UserLifestyleInput(
        transport=TransportInput(
            mode=cast(TransportMode, transport_mode),
            weekly_distance_km=weekly_distance_km,
        ),
        energy=EnergyInput(
            monthly_electricity_kwh=monthly_electricity_kwh,
            cooking_fuel=cast(CookingFuel, cooking_fuel),
        ),
        diet=DietInput(diet_type=cast(DietType, diet_type)),
    )


def render_results(result: FootprintResult, story: StoryCard) -> None:
    """Render the AI Awareness Card: metric, breakdown, equivalents, narrative."""
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


def render_recommendations(result: FootprintResult, lifestyle: UserLifestyleInput) -> None:
    """Render the on-demand reduction tips button and its output."""
    if st.button(
        "How can I reduce this? 🌱",
        key="get_recommendations_btn",
        help=(
            "Get personalised, evidence-based suggestions for reducing "
            "your footprint — tailored to your biggest contributor."
        ),
    ):
        with st.spinner("Putting together a few ideas..."):
            tips = generate_recommendations(result, lifestyle)
        st.markdown("**A few places to start:**")
        for tip in tips:
            st.write(f"- {tip}")


# ---------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------

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

# Layer 1 - collect inputs
transport_mode, weekly_distance_km = render_transport_inputs()
monthly_electricity_kwh, cooking_fuel = render_energy_inputs()
diet_type = render_diet_inputs()

st.divider()

# Layers 2 + 3 - calculate then build the story
if st.button(
    "See my footprint ➜",
    type="primary",
    key="calculate_footprint_btn",
    help="Calculate your estimated monthly carbon footprint based on the inputs above.",
):
    try:
        lifestyle = build_lifestyle_input(
            transport_mode, weekly_distance_km,
            monthly_electricity_kwh, cooking_fuel,
            diet_type,
        )
        result = calculate_footprint(lifestyle)
        story = build_story(result)

        # Stash in session_state so results survive the rerun Streamlit
        # triggers on every interaction.
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

# Layer 3 output + Layer 4 on-demand button
if "result" in st.session_state:
    render_results(st.session_state["result"], st.session_state["story"])
    render_recommendations(st.session_state["result"], st.session_state["lifestyle"])
