"""
Small shared helpers. Nothing in here is carbon-specific - it's just
plumbing other backend files reuse, so it doesn't belong in any one
of them.

No .env handling here on purpose - this project's only secret
(ANTHROPIC_API_KEY) is entirely optional, and when you want it,
it's set as a Streamlit Cloud secret (or any host's env var), not
a local file.
"""

import os
from typing import TYPE_CHECKING

from streamlit.errors import StreamlitSecretNotFoundError

if TYPE_CHECKING:
    # Only imported for type hints, never at runtime - this keeps
    # anthropic an optional dependency for anyone not using Layer 4's
    # LLM path, while still giving editors/type-checkers a real type.
    from anthropic import Anthropic


def get_anthropic_api_key() -> str | None:
    """
    Returns the API key, checking in order:
      1. Environment variable (works locally via .env, and on Hugging
         Face Spaces, where Repository secrets land as real env vars)
      2. Streamlit secrets (st.secrets) - this is how Streamlit
         Community Cloud exposes secrets, NOT as raw env vars
    Returns None if neither has it configured - callers must handle
    that case (see recommendations.py's rule-based fallback).
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        return api_key

    try:
        import streamlit as st
        return st.secrets.get("ANTHROPIC_API_KEY")
    except StreamlitSecretNotFoundError:
        # No secrets.toml configured at all - perfectly normal for
        # local runs or hosts (like HF Spaces) that use env vars instead.
        return None


def get_anthropic_client() -> "Anthropic | None":
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