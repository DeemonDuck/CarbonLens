"""
Integration test for the Streamlit app, using Streamlit's own headless
AppTest framework (no browser needed).

This exists for one reason: to catch UI-breaking regressions before
they ship. Unit tests in test_calculator.py prove the math is correct
in isolation - this proves the actual user flow (fill form -> see
footprint -> ask for tips) still works end to end.
"""

from streamlit.testing.v1 import AppTest


def _run_app():
    at = AppTest.from_file("frontend/app.py")
    at.run()
    return at


def test_app_loads_without_error():
    at = _run_app()
    assert not at.exception


def test_default_submission_shows_footprint_metric():
    at = _run_app()
    at.button[0].click().run()

    assert not at.exception
    assert "result" in at.session_state
    assert len(at.metric) == 1
    assert "kg CO" in at.metric[0].value


def test_breakdown_percentages_render_for_all_three_categories():
    at = _run_app()
    at.button[0].click().run()

    rendered_text = " ".join(m.value for m in at.markdown)
    for category in ("Transport", "Energy", "Diet"):
        assert category in rendered_text


def test_reduction_tips_button_renders_suggestions():
    at = _run_app()
    at.button[0].click().run()
    at.button[1].click().run()

    assert not at.exception
    rendered_text = " ".join(m.value for m in at.markdown)
    assert "A few places to start" in rendered_text


def test_walk_or_cycle_transport_choice_still_validates():
    """
    Regression guard: the zero-emission transport option (walk/cycle)
    must not break validation just because its emission factor is 0.
    """
    at = _run_app()
    at.selectbox[0].select("Mostly walk or cycle").run()
    at.button[0].click().run()

    assert not at.exception
    assert "result" in at.session_state