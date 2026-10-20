"""Explain the statuses without running a new analysis."""

from __future__ import annotations

import streamlit as st


def guide_page() -> None:
    st.header("How to read a result")
    st.markdown(
        "The comparison page only reads the notices you paste. "
        "A status describes those notices. It does not decide what is true outside them."
    )

    st.subheader("Statuses")
    rows = [
        (
            "Consistent",
            "No material contradiction was found in the points this check can compare, and at least one point is shared. Agreement inside the texts is not outside proof.",
        ),
        (
            "Conflicting",
            "The supplied texts disagree on a compared point, such as two different dates. The check does not choose which notice is newer.",
        ),
        (
            "Insufficient evidence",
            "The texts do not establish the answer. A missing fact is not treated as agreement.",
        ),
        (
            "Analysis failed",
            "The live wording step did not return a usable result. No findings are attached. The text stays in the form.",
        ),
    ]
    for title, body in rows:
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.markdown(body)

    st.subheader("Demo and live")
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown("**Demo mode — deterministic example analysis**")
            st.markdown(
                "Fixed rules compare dates, times, places, and amounts. "
                "Kiswahili and Sheng wording comes from fixed templates. "
                "This mode does not call a model and does not translate freely."
            )
    with right:
        with st.container(border=True):
            st.markdown("**Live model**")
            st.markdown(
                "The configured model may rewrite the explanation. "
                "It cannot hide a date, time, place, or amount conflict found by the rules. "
                "A schema-valid reply can still be wrong."
            )

    st.subheader("Reading level")
    st.markdown(
        "Simple uses shorter sentences. Standard adds one sentence of context. "
        "Neither reading level adds facts. Change the language or reading level on Compare notices, then analyze again."
    )
