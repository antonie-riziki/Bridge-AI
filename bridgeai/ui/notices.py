"""Notice text that stays available after Streamlit clears widget state on a page change."""

from __future__ import annotations

import streamlit as st

NOTICE_DEFAULTS = {
    "label_a": "Clinic announcement",
    "text_a": "",
    "label_b": "Community notice",
    "text_b": "",
}


def seed_notice_widgets() -> None:
    """Restore notice widgets from the last values saved on either page."""
    for key, default in NOTICE_DEFAULTS.items():
        durable = f"notice_{key}"
        if key not in st.session_state:
            if durable in st.session_state:
                st.session_state[key] = st.session_state[durable]
            else:
                st.session_state[key] = default


def remember_notices() -> None:
    """Copy the current notice widgets into keys that survive a page change."""
    for key in NOTICE_DEFAULTS:
        if key in st.session_state:
            st.session_state[f"notice_{key}"] = st.session_state[key]
