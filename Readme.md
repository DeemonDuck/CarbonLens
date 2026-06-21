# 🌍 CarbonLens

[![CI](https://github.com/DeemonDuck/CarbonLens/actions/workflows/ci.yml/badge.svg)](https://github.com/DeemonDuck/CarbonLens/actions/workflows/ci.yml)

**See the weight of your everyday choices — without being nagged about them.**

🔗 **Live demo:** [carbon-lens-1.streamlit.app](https://carbon-lens-1.streamlit.app/)

Most carbon footprint tools ask you to log every meal, every commute, every
kWh, forever. People try it for three days and quit. This app does the
opposite: answer a handful of honest questions *once*, and get back a
number you can actually feel — not a spreadsheet row, a story.

---

## Why this exists

Carbon calculators aren't rare. What's rare is one that respects the
person using it. Most tools fail in one of two ways: they either bury you
in daily logging until you give up, or they spit out a raw number like
"437 kg CO₂" that means nothing to anyone who isn't already a climate
researcher.

This project is built on a simple bet: **people don't need more tracking,
they need more feeling.** If a number doesn't connect to something real —
a road trip, a tree, a phone charge — it doesn't change behavior. It just
sits there.

So instead of a tracker, this is a mirror. Answer once. See where you
stand, in terms that actually land. If you're curious how to bring it
down, that's one click away — never forced, never guilt-tripped.

---

## What it actually does

1. **You answer a short form** — how you mostly get around, your monthly
   electricity usage, what you cook with, and your general diet pattern.
   That's it. No daily check-ins.

2. **It calculates your estimated monthly footprint** using real, sourced
   emission factors — India's grid emission factor from the Central
   Electricity Authority, fuel combustion factors from the GHG Protocol,
   and figures from published diet-footprint studies. Not made-up
   multipliers.

3. **It tells you the story behind the number.** Instead of "437 kg CO₂",
   you get: *"That's like driving from Delhi to Jaipur and back 4 times.
   Energy is doing most of the damage here — 54% of your total."*

4. **If you're curious, you can ask "how do I reduce this?"** — and only
   then does the app offer specific, grounded suggestions tied to what's
   actually driving your number. No one's watching you do it. No streaks.
   No shame.

---

## How it's built

The whole thing is one Streamlit app, but internally it's split into
clean layers — each one only knows about the layer right before it, never
about how the UI works or how the math underneath it was done. That
separation is what makes the project easy to extend (swap the frontend,
add a new input category, change an emission factor) without rewriting
everything else.

| Layer | What it does | File |
|---|---|---|
| **1. Input Collection** | Validates what the user enters before anything else touches it | `backend/schemas.py` |
| **2. Emission Calculation** | Turns validated input into kg CO₂, broken down by category | `backend/calculator.py`, `backend/emission_factors.py` |
| **3. Awareness Translator** | Converts the raw number into relatable comparisons + a short narrative, returned as a typed `StoryCard` | `backend/awareness.py` |
| **4. On-Demand Tips** | Generates reduction suggestions — only when asked, never automatically | `backend/recommendations.py` |

Every layer's input and output is a typed Pydantic model — including
the "story card" Layer 3 hands to the UI — so a typo in a field name
fails loudly at construction time instead of silently breaking a render
somewhere downstream. Human-readable labels (what a user sees in a
dropdown vs. what the system stores) live in exactly one place too,
in `backend/schemas.py`, so the frontend never maintains its own
duplicate copy that can drift out of sync.

Layer 4 quietly upgrades itself: if an Anthropic API key is configured, it
generates tips personalized to your exact numbers using Claude. If not
(the default), it falls back to curated, category-specific tips — so the
app works fully out of the box, no API key required.

---

## Accessibility

Accessibility is treated as a first-class concern, not an afterthought.
The decisions below are deliberate and verifiable in the source.

### Widget labelling

Every interactive widget in `frontend/app.py` carries:

- **A visible label** (`label_visibility="visible"`) — labels are never
  hidden or replaced by placeholder text, so screen readers always
  announce what a field is for.
- **A `help=` tooltip** on every input — not just "what to enter" but
  *why* we're asking, in plain language (e.g. *"Found on your electricity
  bill, usually labeled 'units consumed.'"*). This benefits users with
  cognitive disabilities or anyone unfamiliar with carbon terminology.
- **A stable `key=`** on every widget — prevents anonymous, auto-generated
  widget IDs in Streamlit's accessibility tree, making the DOM consistent
  and predictable across reruns.

### Section context

Each input group (Transport, Energy, Diet) opens with an `st.caption()`
paragraph that explains what the group measures and why, before the user
encounters the inputs themselves. Users with screen readers or cognitive
disabilities benefit from understanding the *purpose* of a group before
navigating into it.

### Page title

`st.set_page_config` sets a descriptive title —
*"CarbonLens — Estimate your monthly carbon footprint"* — rather than a
bare app name. This is what screen readers announce as the document title
and what appears in browser history and bookmarks.

### Error messages

Validation errors distinguish between three failure types with specific,
actionable messages:
- `ValueError` → "One of your inputs is outside the expected range: ..."
- `KeyError` → "An unrecognised option was selected ..."
- Unexpected `Exception` → "Something went wrong while calculating ..."

Generic "something went wrong" messages are inaccessible because they
give users no indication of what to do next.

### Colour contrast (WCAG 2.1 AA)

The theme in `.streamlit/config.toml` was chosen specifically to meet or
exceed the WCAG 2.1 AA minimum contrast ratio of 4.5:1 for normal text:

| Pair | Contrast ratio | AA pass? |
|---|---|---|
| `#1B1B1B` text on `#FFFFFF` background | ~18.1:1 | ✅ (exceeds AAA) |
| `#1B1B1B` text on `#F1F8E9` secondary background | ~15.3:1 | ✅ (exceeds AAA) |
| `#2E7D32` primary (buttons) on `#FFFFFF` | ~7.2:1 | ✅ (exceeds AAA) |

### Typography

`font = "sans serif"` is explicitly set in `config.toml`. Sans-serif
typefaces score higher on legibility measures for users with dyslexia or
low vision (British Dyslexia Association style guide), compared to
decorative or monospaced alternatives.

### Streamlit platform constraints

Streamlit renders into a React shell. Custom ARIA roles, landmark
regions, and `aria-label` attributes are not directly configurable from
Python — they are managed by Streamlit's own component library. The
decisions above represent the full extent of what is achievable within
that constraint while still staying within Streamlit's supported API.

---

## Tech stack

- **Python** end to end
- **Streamlit** for the UI
- **Pydantic** for strict, self-documenting data validation between layers
- **Anthropic API** (optional) for personalized reduction tips
- **Pytest** for testing — including a headless Streamlit `AppTest`
  suite that simulates real clicks without a browser
- **mypy** + **ruff** for type-checking and linting, enforced in CI

---

## Project structure

```
carbon-lens-app/
├── .github/
│   └── workflows/
│       └── ci.yml             # lint + type-check + tests, on every push
├── frontend/
│   └── app.py              # Streamlit UI - orchestrates all layers
├── backend/
│   ├── schemas.py           # data contracts between layers + UI labels
│   ├── emission_factors.py  # sourced reference constants
│   ├── calculator.py        # Layer 2 - the carbon math
│   ├── awareness.py         # Layer 3 - equivalents + story builder
│   ├── recommendations.py   # Layer 4 - tips, LLM + rule-based fallback
│   └── utils.py              # optional Anthropic client helper
├── .streamlit/
│   └── config.toml           # app theme (WCAG 2.1 AA contrast, sans-serif font)
├── assets/                   # icons, demo GIFs, screenshots
├── tests/
│   ├── test_calculator.py    # Layer 2 - the math + all modes/fuels/edge cases
│   ├── test_awareness.py     # Layer 3 - story/equivalents + all dominant categories
│   ├── test_recommendations.py  # Layer 4 - mocked LLM + all failure paths
│   └── test_app.py            # full UI flow, headless (no browser)
├── pyproject.toml             # ruff + mypy + pytest config
├── requirements.txt           # what the deployed app needs
├── requirements-dev.txt       # + pytest/ruff/mypy, local dev only
└── .gitignore
```

---

## Running it locally

```bash
pip install -r requirements.txt
streamlit run frontend/app.py
```

Works immediately, no setup required. Want to try the LLM-personalized
tips locally instead of the rule-based fallback?

```bash
export ANTHROPIC_API_KEY=your_key_here   # macOS/Linux
streamlit run frontend/app.py
```

## Deploying on Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. **New app** → select this repo and branch → set main file path to `frontend/app.py`.
4. Deploy. `requirements.txt` installs automatically — no `.env`, no
   separate backend service needed.
5. *(Optional)* To enable LLM-personalized tips on the live app, go to
   **Settings → Secrets** and add:
   ```toml
   ANTHROPIC_API_KEY = "your_key_here"
   ```

## Running tests, lint, and type-checks

```bash
pip install -r requirements-dev.txt
pytest tests/ -v        # 56 tests across all 4 layers + full UI flow
ruff check .             # lint
mypy backend/            # type-check
```

All three run automatically on every push via `.github/workflows/ci.yml`.

---

## What's next

A "what-if" explorer is on the roadmap — letting someone swap a single
choice (say, their commute mode) and instantly see how the number shifts,
framed as curiosity rather than a target to hit. Reuses the existing
calculation engine entirely; no new emission-factor work needed.

---

## Built by

**Team DeemonDuck**
GitHub: [github.com/DeemonDuck](https://github.com/DeemonDuck)
