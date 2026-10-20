"""List place phrases and plot only coordinates the user supplies."""

from __future__ import annotations

import streamlit as st

from bridgeai.services.evidence import InputError, validate_source_pairs
from bridgeai.services.places import CoordinateError, listed_places, validate_coordinates
from bridgeai.ui.notices import NOTICE_DEFAULTS


def places_page() -> None:
    st.header("Places")
    st.markdown(
        "This page lists place phrases the check can see in the notices, such as “market ground”. "
        "It does not look those words up on a map. A pin is drawn only from latitude and longitude you enter."
    )

    _seed_place_fields()
    left, right = st.columns(2, gap="large")
    with left:
        with st.container(border=True):
            st.markdown("**Source 1**")
            st.text_input("Label for source 1", key="place_label_a")
            st.text_area("Text for source 1", key="place_text_a", height=180, max_chars=8000)
    with right:
        with st.container(border=True):
            st.markdown("**Source 2**")
            st.text_input("Label for source 2", key="place_label_b")
            st.text_area("Text for source 2", key="place_text_b", height=180, max_chars=8000)
    _remember_place_fields()
    st.caption("These are the same notices as on Compare notices. Editing them here updates that page too.")

    mentions = _mentions()
    st.subheader("Place phrases in the text")
    if mentions is None:
        st.info("Add both notices to list places. Empty text is not treated as a location.")
    elif not mentions:
        st.info("No place phrase was found. That is not the same as knowing where something happened.")
    else:
        grouped: dict[str, list] = {}
        for mention in mentions:
            grouped.setdefault(mention.source_label, []).append(mention)
        columns = st.columns(max(len(grouped), 1), gap="large")
        for column, (label, items) in zip(columns, grouped.items(), strict=False):
            with column:
                with st.container(border=True):
                    st.markdown(f"**{label}**")
                    for item in items:
                        st.markdown(item.place)
                        st.caption("Quoted text: “" + item.excerpt.replace(":", r"\:") + "”")

    st.subheader("Coordinates you already know")
    st.markdown(
        "Optional. Leave both fields empty if you do not have coordinates. "
        "These numbers are not read from the notice."
    )
    pin_cols = st.columns(2, gap="large")
    pins: list[dict[str, float | str]] = []
    errors: list[str] = []
    for column, suffix, label_key, default_label in (
        (pin_cols[0], "a", "place_label_a", "Source 1"),
        (pin_cols[1], "b", "place_label_b", "Source 2"),
    ):
        with column:
            label = st.session_state.get(label_key) or default_label
            st.markdown(f"**{label}**")
            lat = st.text_input(f"Latitude for {label}", key=f"lat_{suffix}")
            lon = st.text_input(f"Longitude for {label}", key=f"lon_{suffix}")
            try:
                pin = validate_coordinates(lat, lon)
            except CoordinateError as exc:
                errors.append(f"{label}: {exc}")
                continue
            if pin is not None:
                pins.append({"lat": pin[0], "lon": pin[1], "label": label})

    for message in errors:
        st.error(message)

    if pins:
        st.map([{"lat": pin["lat"], "lon": pin["lon"]} for pin in pins], latitude="lat", longitude="lon")
        st.caption("Each pin uses coordinates you entered. It was not found in the notice and it is not a verification.")
        for pin in pins:
            st.markdown(f"- **{pin['label']}**: {pin['lat']}, {pin['lon']} — entered by you, not taken from the text.")
    else:
        st.info("The map stays empty until you enter a valid latitude and longitude. No city is assumed.")


_PLACE_FIELDS = {
    "place_label_a": "label_a",
    "place_text_a": "text_a",
    "place_label_b": "label_b",
    "place_text_b": "text_b",
}


def _seed_place_fields() -> None:
    for widget_key, notice_key in _PLACE_FIELDS.items():
        durable = f"notice_{notice_key}"
        if widget_key not in st.session_state:
            if durable in st.session_state:
                st.session_state[widget_key] = st.session_state[durable]
            else:
                st.session_state[widget_key] = NOTICE_DEFAULTS[notice_key]


def _remember_place_fields() -> None:
    for widget_key, notice_key in _PLACE_FIELDS.items():
        if widget_key in st.session_state:
            st.session_state[f"notice_{notice_key}"] = st.session_state[widget_key]


def _mentions():
    try:
        sources = validate_source_pairs(
            [
                (st.session_state.get("place_label_a", ""), st.session_state.get("place_text_a", "")),
                (st.session_state.get("place_label_b", ""), st.session_state.get("place_text_b", "")),
            ]
        )
    except InputError:
        return None
    return listed_places(sources)
