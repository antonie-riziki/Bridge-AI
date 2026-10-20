"""State the boundaries of the prototype. This page does not analyze text."""

from __future__ import annotations

import streamlit as st


def limits_page() -> None:
    st.header("Limits")
    st.markdown(
        "BridgeAI is an evidence assistant for notices you paste. "
        "It is not a news verifier, a medical service, or an emergency line."
    )

    limits = [
        "It does not search the web, call an organization, or look up a phone number.",
        "It does not invent contacts, links, or coordinates.",
        "A claim repeated by more than one source is still not independent proof.",
        "Silence in one notice is not agreement.",
        "Demo-mode Kiswahili and Sheng come from fixed templates. They have not been independently validated.",
        "Live model wording has not been independently checked. A valid response can be wrong.",
        "Place names in a notice are not turned into map pins. A pin appears only when you enter coordinates you already know.",
        "Source text stays in this browser session. It is not written to a database.",
    ]
    for item in limits:
        st.markdown(f"- {item}")

    st.subheader("What to do with a gap or a conflict")
    st.markdown(
        "Use a phone number or address you already trust, and ask the organization that issued the notice. "
        "Do not treat a contact printed only inside an unverified text as official."
    )
