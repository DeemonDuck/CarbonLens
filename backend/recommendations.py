"""
Layer 4 - On-Demand Reduction Tips
--------------------------------------
This layer ONLY runs when the user clicks "How can I reduce this?" -
never automatically. That's the whole philosophy of this app: show
the truth, then let curiosity (not guilt) drive the next step.

Two tiers, by design:
  1. Rule-based tips (RULE_BASED_TIPS) - always available, zero cost,
     zero dependencies. The demo works even with no API key set.
  2. LLM-generated tips - if ANTHROPIC_API_KEY is configured, we ask
     Claude to generate more specific, fact-grounded suggestions
     tailored to the user's actual numbers instead of generic advice.

If the LLM call fails for any reason (no key, network issue, rate
limit), we silently fall back to tier 1. The user should never see
a broken feature - just a slightly less personalized one.
"""

from backend.schemas import FootprintResult, UserLifestyleInput
from backend.utils import get_anthropic_client

RULE_BASED_TIPS = {
    "transport": [
        "Swap one or two car trips a week for public transport - "
        "even partial switches add up monthly.",
        "Combine errands into a single trip instead of multiple short drives.",
        "If your commute is under 3km, walking or cycling it removes "
        "that trip's emissions entirely.",
    ],
    "energy": [
        "Switch to LED bulbs if you haven't already - lighting is one "
        "of the easiest wins on an electricity bill.",
        "Unplug devices on standby; phantom load adds up over a month.",
        "If you cook with LPG, a pressure cooker for daals/grains cuts "
        "cooking time (and gas use) significantly.",
    ],
    "diet": [
        "Try 2-3 plant-based days a week instead of a full diet overhaul - "
        "smaller shifts are easier to sustain.",
        "Reducing red meat specifically moves the needle more than "
        "cutting any other single food group.",
        "Local, seasonal produce typically has a smaller footprint than "
        "out-of-season imported items.",
    ],
}

