"""Streamlit interface for the BridgeAI evidence check."""

from __future__ import annotations

import json

import streamlit as st

from bridgeai.config import provider_available, public_provider_status
from bridgeai.schemas import AnalysisResult, Language, ReadingLevel, ResolutionStatus
from bridgeai.services.agent import analyze_pairs
from bridgeai.services.evidence import InputError
from bridgeai.services.language import status_label
from bridgeai.services.scenarios import SCENARIOS

LANGUAGES = [
    ("English", Language.ENGLISH),
    ("Kiswahili", Language.KISWAHILI),
    ("Sheng (best effort)", Language.SHENG),
]
READINGS = [
    ("Simple — short sentences", ReadingLevel.SIMPLE),
    ("Standard — a bit more context", ReadingLevel.STANDARD),
]
UI = {
    Language.ENGLISH: {
        "sources": "Sources",
        "claims": "Claims found in the supplied text",
        "compare": "Agreements and conflicts",
        "agreements": "Agreements",
        "conflicts": "Conflicts",
        "unresolved": "What is still open",
        "explanation": "Explanation",
        "next": "Recommended next step",
        "limits": "Limitations and mode",
        "trail": "Evidence trail",
        "empty_claims": "No comparable date, time, place, or amount was found.",
        "none": "None in this check.",
    },
    Language.KISWAHILI: {
        "sources": "Vyanzo",
        "claims": "Madai yaliyopatikana katika maandishi",
        "compare": "Makubaliano na migongano",
        "agreements": "Makubaliano",
        "conflicts": "Migongano",
        "unresolved": "Mambo ambayo bado hayajafahamika",
        "explanation": "Maelezo",
        "next": "Hatua inayopendekezwa",
        "limits": "Mipaka na hali ya ukaguzi",
        "trail": "Njia ya ushahidi",
        "empty_claims": "Hakuna tarehe, saa, mahali, au kiasi kilichoweza kulinganishwa.",
        "none": "Hakuna katika ukaguzi huu.",
    },
    Language.SHENG: {
        "sources": "Sources",
        "claims": "Claims zilizopatikana kwa text",
        "compare": "Agreements na conflicts",
        "agreements": "Agreements",
        "conflicts": "Conflicts",
        "unresolved": "Vitu ambavyo bado wazi",
        "explanation": "Explanation",
        "next": "Next step",
        "limits": "Limits na mode",
        "trail": "Evidence trail",
        "empty_claims": "Hakuna date, time, place, ama kiasi ya kulinganisha.",
        "none": "Hakuna kwa hii check.",
    },
}


def main() -> None:
    st.set_page_config(page_title="BridgeAI", page_icon="B", layout="wide")
    _inject_css()
    _init_state()

    st.title("BridgeAI")
    st.markdown(
        "An evidence assistant for community notices. It compares what two texts **say**, "
        "and keeps that separate from what anyone has **established**."
    )
    st.caption(
        "BASIX State of the Art Hackathon · Omega AI Agents · The Agent Without Borders. "
        "Reasoning that stays explicit across language, reading level, and a missing live model."
    )

    st.info(
        "BridgeAI can compare the notices you paste, quote them, and point out agreement, "
        "contradiction, or a gap. It cannot verify news, give medical advice, or handle an emergency. "
        "It does not look up contacts, and it does not treat a repeated claim as proof."
    )

    live = provider_available()
    if not live:
        st.session_state.analysis_mode = "demo"
    _demo_banner(st.session_state.analysis_mode, live)

    _sample_buttons()
    language, reading = _selectors(live)
    label_a, text_a, label_b, text_b = _source_fields()

    clicked = st.button("Analyze evidence", type="primary", use_container_width=True)
    queued = st.session_state.get("queued_scenario")
    if queued:
        st.session_state.queued_scenario = None
    if clicked or queued:
        _run(label_a, text_a, label_b, text_b, language, reading)

    _show_output(label_a, text_a, label_b, text_b, language, reading)


def _init_state() -> None:
    defaults = {
        "label_a": "Clinic announcement",
        "text_a": "",
        "label_b": "Community notice",
        "text_b": "",
        "language_choice": "English",
        "reading_choice": "Simple — short sentences",
        "analysis_mode": "demo",
        "queued_scenario": None,
        "last_result": None,
        "last_fingerprint": None,
        "last_error": None,
        "error_fingerprint": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _demo_banner(mode: str, live: bool) -> None:
    if mode == "demo" or not live:
        st.info("Demo mode — deterministic example analysis")
        st.caption(
            "This mode uses fixed rules for dates, times, places, and amounts. "
            "It is not a live model and it does not translate freely."
        )
        if not live:
            status = public_provider_status()
            st.caption(
                "No live model is configured"
                + ("" if status["enabled_flag"] else " because the provider flag is off")
                + ". A local ASI_API_KEY turns on live wording when you are ready."
            )
    else:
        status = public_provider_status()
        st.info(
            "Live model available. Structured values are still checked with deterministic rules."
        )
        st.caption(f"Configured model name: {status['model']}. The key stays in the local environment.")


def _sample_buttons() -> None:
    st.subheader("Sample scenarios")
    st.markdown("Load a community-information example and run it in one step.")
    columns = st.columns(3)
    for column, scenario in zip(columns, SCENARIOS.values(), strict=True):
        with column:
            st.markdown(f"**{scenario.title}**")
            st.caption(scenario.description)
            st.button(
                f"Run {scenario.title}",
                key=f"run_{scenario.scenario_id}",
                on_click=_queue_scenario,
                args=(scenario.scenario_id,),
                use_container_width=True,
            )


def _queue_scenario(scenario_id: str) -> None:
    scenario = SCENARIOS[scenario_id]
    st.session_state.label_a = scenario.label_a
    st.session_state.text_a = scenario.text_a
    st.session_state.label_b = scenario.label_b
    st.session_state.text_b = scenario.text_b
    st.session_state.queued_scenario = scenario_id


def _selectors(live: bool) -> tuple[Language, ReadingLevel]:
    left, right = st.columns(2)
    with left:
        if live:
            st.radio(
                "Analysis mode",
                options=["live", "demo"],
                format_func=lambda value: (
                    "Live model" if value == "live" else "Demo mode — deterministic example analysis"
                ),
                key="analysis_mode",
                horizontal=True,
            )
        language_label = st.selectbox(
            "Response language",
            options=[label for label, _ in LANGUAGES],
            key="language_choice",
            help="The explanation is written in this language. Dates and amounts stay in their original form.",
        )
    with right:
        reading_label = st.radio(
            "Reading level",
            options=[label for label, _ in READINGS],
            key="reading_choice",
            help="Simple uses shorter sentences. Standard adds one sentence of context. Neither adds facts.",
        )
    language = dict(LANGUAGES)[language_label]
    reading = dict(READINGS)[reading_label]
    st.caption("Language and reading level apply when you analyze. Change them, then analyze again.")
    return language, reading


def _source_fields() -> tuple[str, str, str, str]:
    st.subheader("Sources")
    st.markdown(
        "Paste notices, announcements, or short statements. Text inside a source is evidence. "
        "It cannot change the rules of the check."
    )
    left, right = st.columns(2)
    with left:
        label_a = st.text_input("Label for source 1", key="label_a")
        text_a = st.text_area(
            "Text for source 1",
            key="text_a",
            height=220,
            max_chars=8000,
            help="For example, a clinic announcement. Up to 8000 characters.",
        )
        st.caption(f"{len(text_a)} / 8000 characters")
    with right:
        label_b = st.text_input("Label for source 2", key="label_b")
        text_b = st.text_area(
            "Text for source 2",
            key="text_b",
            height=220,
            max_chars=8000,
            help="For example, a community notice. Up to 8000 characters.",
        )
        st.caption(f"{len(text_b)} / 8000 characters")
    return label_a, text_a, label_b, text_b


def _run(
    label_a: str,
    text_a: str,
    label_b: str,
    text_b: str,
    language: Language,
    reading: ReadingLevel,
) -> None:
    mode = "demo" if st.session_state.analysis_mode == "demo" or not provider_available() else "live"
    fingerprint = _fingerprint(label_a, text_a, label_b, text_b, language, reading, mode)
    try:
        with st.spinner("Comparing the supplied text…"):
            result = analyze_pairs(
                [(label_a, text_a), (label_b, text_b)],
                response_language=language,
                reading_level=reading,
                mode=mode,  # type: ignore[arg-type]
            )
    except InputError as exc:
        st.session_state.last_error = str(exc)
        st.session_state.error_fingerprint = fingerprint
        return
    except Exception:
        st.session_state.last_error = (
            "The check stopped before it could produce a result. Your text is still in the form."
        )
        st.session_state.error_fingerprint = fingerprint
        return

    st.session_state.last_result = result.model_dump(mode="json")
    st.session_state.last_fingerprint = fingerprint
    st.session_state.last_error = None
    st.session_state.error_fingerprint = None


def _show_output(
    label_a: str,
    text_a: str,
    label_b: str,
    text_b: str,
    language: Language,
    reading: ReadingLevel,
) -> None:
    mode = "demo" if st.session_state.analysis_mode == "demo" or not provider_available() else "live"
    fingerprint = _fingerprint(label_a, text_a, label_b, text_b, language, reading, mode)
    if st.session_state.last_error and st.session_state.error_fingerprint == fingerprint:
        st.error(st.session_state.last_error)

    payload = st.session_state.last_result
    if not payload:
        st.markdown("Run a sample scenario, or paste two sources, then analyze the evidence.")
        return
    if st.session_state.last_fingerprint != fingerprint:
        st.info(
            "The form has changed since the last result. That result is hidden so it is not read as a check of the text now on screen. Analyze again."
        )
        return

    result = AnalysisResult.model_validate(payload)
    copy = UI[result.response_language]
    _status_block(result)
    if result.overall_status == ResolutionStatus.ANALYSIS_FAILED:
        st.subheader(copy["explanation"])
        st.text(result.concise_summary)
        st.subheader(copy["next"])
        st.text(result.recommended_next_step)
        _limitations(result, copy)
        return

    st.subheader(copy["explanation"])
    st.text(result.concise_summary)
    st.subheader(copy["next"])
    st.text(result.recommended_next_step)

    st.subheader(copy["claims"])
    if not result.claims:
        st.text(copy["empty_claims"])
    else:
        grouped: dict[str, list] = {}
        for claim in result.claims:
            grouped.setdefault(claim.source_label, []).append(claim)
        columns = st.columns(max(len(grouped), 1))
        for column, (label, claims) in zip(columns, grouped.items(), strict=False):
            with column:
                st.text(label)
                for claim in claims:
                    st.text(claim.claim_text)
                    st.caption(f"Quoted text: “{_plain(claim.excerpt)}”")

    st.subheader(copy["compare"])
    left, right = st.columns(2)
    with left:
        st.markdown(f"**{copy['agreements']}**")
        if result.detected_agreements:
            for item in result.detected_agreements:
                st.text(item.summary)
        else:
            st.text(copy["none"])
    with right:
        st.markdown(f"**{copy['conflicts']}**")
        if result.detected_conflicts:
            for item in result.detected_conflicts:
                st.text(item.summary)
                for source_id, value in item.values_by_source.items():
                    st.caption(f"{source_id}: {_plain(value)}")
        else:
            st.text(copy["none"])

    st.subheader(copy["unresolved"])
    if result.unresolved_questions:
        for question in result.unresolved_questions:
            st.text(question)
    else:
        st.text(copy["none"])

    st.subheader(copy["trail"])
    if not result.evidence_references:
        st.text(copy["empty_claims"])
    for reference in result.evidence_references:
        st.text(f"{reference.source_label} · {reference.reference_id}")
        st.text(f"“{reference.excerpt}”")
        if reference.note:
            st.caption(_plain(reference.note))

    _limitations(result, copy)


def _status_block(result: AnalysisResult) -> None:
    label = status_label(result.overall_status, result.response_language)
    if result.overall_status == ResolutionStatus.CONSISTENT:
        st.success(label)
    elif result.overall_status == ResolutionStatus.INSUFFICIENT_EVIDENCE:
        st.warning(label)
    else:
        st.error(label)


def _limitations(result: AnalysisResult, copy: dict[str, str]) -> None:
    st.subheader(copy["limits"])
    if result.provider_mode.value == "demo":
        st.info("Demo mode — deterministic example analysis")
    else:
        st.caption(
            "Provider mode: live. This is model wording plus deterministic checks, not an external verification."
        )
    for item in result.limitations:
        st.text(item)


def _plain(value: str) -> str:
    """Keep times intact. Streamlit markdown treats some colon pairs as emoji codes."""
    return value.replace(":", r"\:")


def _fingerprint(
    label_a: str,
    text_a: str,
    label_b: str,
    text_b: str,
    language: Language,
    reading: ReadingLevel,
    mode: str,
) -> str:
    payload = {
        "label_a": label_a,
        "text_a": text_a,
        "label_b": label_b,
        "text_b": text_b,
        "language": language.value,
        "reading": reading.value,
        "mode": mode,
    }
    return json.dumps(payload, sort_keys=True)


def _inject_css() -> None:
    st.markdown(
        """
        <style>
          .block-container {max-width: 1080px; padding-top: 1.6rem; padding-bottom: 3rem;}
          html, body, [class*="css"] {font-size: 17px;}
          h1 {letter-spacing: -0.03em; font-weight: 680;}
          .bridge-banner {
            background: #0f3d3e;
            color: #f7f4ef;
            border-radius: 10px;
            padding: 0.85rem 1rem;
            font-weight: 650;
            margin: 0.4rem 0 0.6rem 0;
          }
          .bridge-banner.live {background: #243126;}
          .bridge-status {
            border: 2px solid #1c1915;
            border-radius: 12px;
            padding: 0.95rem 1.05rem;
            background: #fffdf8;
            font-weight: 680;
            margin: 0.8rem 0 1rem 0;
          }
          .bridge-status.conflicting {border-color: #8d1d1d; background: #fff5f3;}
          .bridge-status.consistent {border-color: #0d5c3d; background: #f2faf5;}
          .bridge-status.insufficient {border-color: #8a5a00; background: #fff8eb;}
          .bridge-status.failed {border-color: #3f3a33; background: #f4f2ee;}
        </style>
        """,
        unsafe_allow_html=True,
    )
