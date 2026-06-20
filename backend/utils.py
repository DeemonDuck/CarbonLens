"""
Small shared helpers. Nothing in here is carbon-specific - it's just
plumbing other backend files reuse, so it doesn't belong in any one
of them.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # reads .env if present, no-op otherwise


def get_anthropic_api_key() -> str | None:
    """Returns the API key from environment, or None if not configured."""
    return os.getenv("ANTHROPIC_API_KEY")


def get_anthropic_client():
    """
    Returns an Anthropic client if a key is configured, otherwise None.
    Callers MUST handle the None case (see recommendations.py) - we
    never want a missing API key to crash the whole app.
    """
    api_key = get_anthropic_api_key()
    if not api_key:
        return None

    try:
        import anthropic
        return anthropic.Anthropic(api_key=api_key)
    except ImportError:
        return None