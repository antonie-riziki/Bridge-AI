"""Streamlit interface for the BridgeAI evidence check."""

from __future__ import annotations

import html
import json

import streamlit as st

from bridgeai.config import provider_available, public_provider_status
from bridgeai.schemas import AnalysisResult, Language, ReadingLevel, ResolutionStatus
from bridgeai.services.agent import analyze_pairs
from bridgeai.services.evidence import InputError
from bridgeai.services.language import status_label
from bridgeai.services.scenarios import SCENARIOS
from bridgeai.ui.notices import remember_notices, seed_notice_widgets

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
        "samples": "Sample scenarios",
        "samples_help": "Load a community-information example and run it in one step.",
        "settings": "How to explain the result",
        "empty_title": "Nothing compared yet",
        "empty_body": "Run a sample scenario, or paste two sources, then analyze the evidence.",
        "changed": "The form has changed since the last result. That result is hidden so it is not read as a check of the text now on screen. Analyze again.",
        "source_help": "Paste notices, announcements, or short statements. Text inside a source is evidence. It cannot change the rules of the check.",
        "quoted": "Quoted text",
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
        "samples": "Mifano",
        "samples_help": "Chagua mfano na ukague mara moja.",
        "settings": "Jinsi ya kueleza matokeo",
        "empty_title": "Hakuna ulinganisho bado",
        "empty_body": "Tumia mfano, au bandika vyanzo viwili, kisha chambua ushahidi.",
        "changed": "Fomu imebadilika baada ya matokeo ya mwisho. Matokeo hayo yamefichwa. Chambua tena.",
        "source_help": "Bandika matangazo au taarifa fupi. Maandishi ni ushahidi. Hayabadilishi kanuni za ukaguzi.",
        "quoted": "Nukuu",
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
        "samples": "Sample scenarios",
        "samples_help": "Chagua example na u-run mara moja.",
        "settings": "How to explain the result",
        "empty_title": "Hakuna comparison bado",
        "empty_body": "Run sample, ama paste sources mbili, halafu analyze.",
        "changed": "Form imebadilika. Result ya zamani imefichwa. Analyze tena.",
        "source_help": "Paste notice. Text ni evidence. Haiwezi badilisha rules.",
        "quoted": "Quoted text",
    },
}


def compare_page() -> None:
    _init_state()

    _header()
    live = provider_available()
    if not live:
        st.session_state.analysis_mode = "demo"
    _demo_banner(st.session_state.analysis_mode, live)

    _sample_buttons()
    language, reading = _selectors(live)
    label_a, text_a, label_b, text_b = _source_fields(language)

    clicked = st.button("Analyze evidence", type="primary", use_container_width=True)
    queued = st.session_state.get("queued_scenario")
    if queued:
        st.session_state.queued_scenario = None
    if clicked or queued:
        _run(label_a, text_a, label_b, text_b, language, reading)

    st.divider()
    _show_output(label_a, text_a, label_b, text_b, language, reading)


def _header() -> None:
    st.markdown(
        """
        <header class="bridge-hero">
          <p class="bridge-kicker">BASIX · Omega AI Agents · The Agent Without Borders</p>
          <h1>BridgeAI</h1>
          <p class="bridge-lede">Compare what two community notices say, and keep that separate from what anyone has established.</p>
        </header>
        """,
        unsafe_allow_html=True,
    )
    can, cannot = st.columns(2)
    with can:
        with st.container(border=True):
            st.markdown("**What this check can do**")
            st.markdown(
                "Compare the notices you paste, quote the lines it used, and show agreement, a contradiction, or a gap."
            )
    with cannot:
        with st.container(border=True):
            st.markdown("**What it cannot do**")
            st.markdown(
                "Verify news, give medical advice, or handle an emergency. It does not look up contacts, and a repeated claim is not proof."
            )


def _init_state() -> None:
    seed_notice_widgets()
    defaults = {
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
        st.info("Live model available. Structured values are still checked with deterministic rules.")
        st.caption(f"Configured model name: {status['model']}. The key stays in the local environment.")


def _sample_buttons() -> None:
    st.subheader("Sample scenarios")
    st.caption("Load a community-information example and run it in one step.")
    columns = st.columns(3)
    for column, scenario in zip(columns, SCENARIOS.values(), strict=True):
        with column:
            with st.container(border=True):
                st.markdown(f"**{html.escape(scenario.title)}**")
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
    remember_notices()


def _selectors(live: bool) -> tuple[Language, ReadingLevel]:
    st.subheader("How to explain the result")
    if live:
        mode_col, language_col, reading_col = st.columns([1.1, 1, 1.3])
        with mode_col:
            st.radio(
                "Analysis mode",
                options=["live", "demo"],
                format_func=lambda value: (
                    "Live model" if value == "live" else "Demo mode — deterministic example analysis"
                ),
                key="analysis_mode",
            )
    else:
        language_col, reading_col = st.columns(2)
    with language_col:
        language_label = st.selectbox(
            "Response language",
            options=[label for label, _ in LANGUAGES],
            key="language_choice",
            help="The explanation is written in this language. Dates and amounts stay in their original form.",
        )
    with reading_col:
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


def _source_fields(language: Language) -> tuple[str, str, str, str]:
    copy = UI[language]
    st.subheader(copy["sources"])
    st.caption(copy["source_help"])
    left, right = st.columns(2, gap="large")
    with left:
        with st.container(border=True):
            st.markdown('<p class="bridge-kicker">Source 1</p>', unsafe_allow_html=True)
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
        with st.container(border=True):
            st.markdown('<p class="bridge-kicker">Source 2</p>', unsafe_allow_html=True)
            label_b = st.text_input("Label for source 2", key="label_b")
            text_b = st.text_area(
                "Text for source 2",
                key="text_b",
                height=220,
                max_chars=8000,
                help="For example, a community notice. Up to 8000 characters.",
            )
            st.caption(f"{len(text_b)} / 8000 characters")
    remember_notices()
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
    copy = UI[language]
    mode = "demo" if st.session_state.analysis_mode == "demo" or not provider_available() else "live"
    fingerprint = _fingerprint(label_a, text_a, label_b, text_b, language, reading, mode)
    if st.session_state.last_error and st.session_state.error_fingerprint == fingerprint:
        st.error(st.session_state.last_error)

    payload = st.session_state.last_result
    if not payload:
        with st.container(border=True):
            st.subheader(copy["empty_title"])
            _prose(copy["empty_body"])
        return
    if st.session_state.last_fingerprint != fingerprint:
        st.info(copy["changed"])
        return

    result = AnalysisResult.model_validate(payload)
    copy = UI[result.response_language]
    _status_block(result)
    if result.overall_status == ResolutionStatus.ANALYSIS_FAILED:
        _section(copy["explanation"], result.concise_summary)
        _section(copy["next"], result.recommended_next_step)
        _limitations(result, copy)
        return

    answer, action = st.columns([1.4, 1], gap="large")
    with answer:
        _section(copy["explanation"], result.concise_summary)
    with action:
        _section(copy["next"], result.recommended_next_step)

    st.subheader(copy["claims"])
    if not result.claims:
        _prose(copy["empty_claims"])
    else:
        grouped: dict[str, list] = {}
        for claim in result.claims:
            grouped.setdefault(claim.source_label, []).append(claim)
        columns = st.columns(max(len(grouped), 1), gap="large")
        for column, (label, claims) in zip(columns, grouped.items(), strict=False):
            with column:
                with st.container(border=True):
                    st.markdown(f'<p class="bridge-kicker">{html.escape(label)}</p>', unsafe_allow_html=True)
                    for claim in claims:
                        _prose(claim.claim_text)
                        st.caption(f"{copy['quoted']}: “{claim.excerpt}”")

    st.subheader(copy["compare"])
    left, right = st.columns(2, gap="large")
    with left:
        with st.container(border=True):
            st.markdown(f"**{copy['agreements']}**")
            if result.detected_agreements:
                for item in result.detected_agreements:
                    _prose(item.summary)
            else:
                _prose(copy["none"])
    with right:
        with st.container(border=True):
            st.markdown(f"**{copy['conflicts']}**")
            if result.detected_conflicts:
                for item in result.detected_conflicts:
                    _prose(item.summary)
                    for source_id, value in item.values_by_source.items():
                        st.caption(f"{source_id}: {value}")
            else:
                _prose(copy["none"])

    st.subheader(copy["unresolved"])
    if result.unresolved_questions:
        for question in result.unresolved_questions:
            _prose(question)
    else:
        _prose(copy["none"])

    with st.expander(copy["trail"], expanded=True):
        if not result.evidence_references:
            _prose(copy["empty_claims"])
        for reference in result.evidence_references:
            st.markdown(
                f'<p class="bridge-kicker">{html.escape(reference.source_label)} · {html.escape(reference.reference_id)}</p>',
                unsafe_allow_html=True,
            )
            _quote(reference.excerpt)
            if reference.note:
                st.caption(reference.note)

    _limitations(result, copy)


def _section(title: str, body: str) -> None:
    with st.container(border=True):
        st.subheader(title)
        _prose(body)


def _status_block(result: AnalysisResult) -> None:
    label = status_label(result.overall_status, result.response_language)
    if result.overall_status == ResolutionStatus.CONSISTENT:
        st.success(label)
    elif result.overall_status == ResolutionStatus.INSUFFICIENT_EVIDENCE:
        st.warning(label)
    else:
        st.error(label)


def _limitations(result: AnalysisResult, copy: dict[str, str]) -> None:
    with st.expander(copy["limits"], expanded=True):
        if result.provider_mode.value == "demo":
            st.info("Demo mode — deterministic example analysis")
        else:
            st.caption(
                "Provider mode: live. This is model wording plus deterministic checks, not an external verification."
            )
        for item in result.limitations:
            _prose(item)


def _prose(text: str) -> None:
    st.markdown(f'<p class="bridge-prose">{_html_text(text)}</p>', unsafe_allow_html=True)


def _quote(text: str) -> None:
    st.markdown(f'<blockquote class="bridge-quote">{_html_text(text)}</blockquote>', unsafe_allow_html=True)


def _html_text(text: str) -> str:
    return html.escape(text).replace("\n", "<br>")


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


def inject_css() -> None:
    st.markdown(
        """
        <style>
          .block-container {max-width: 1120px; padding-top: 2.6rem; padding-bottom: 4rem;}
          html, body, [class*="css"] {font-size: 17px;}
          [data-testid="stAppDeployButton"], [data-testid="stDeployButton"] {display: none !important;}
          header[data-testid="stHeader"] {background: #f4f0e8;}
          .bridge-hero {margin: 0 0 0.4rem 0;}
          .bridge-hero h1 {
            letter-spacing: -0.04em;
            font-weight: 680;
            font-size: 3rem;
            line-height: 1.05;
            margin: 0.15rem 0 0.45rem 0;
            color: #142321;
          }
          .bridge-kicker {
            color: #0f3d3e;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin: 0 0 0.35rem 0;
          }
          .bridge-lede {
            color: #3f3a33;
            font-size: 1.2rem;
            line-height: 1.45;
            max-width: 42rem;
            margin: 0 0 0.8rem 0;
          }
          .bridge-prose {
            color: #1c1915;
            line-height: 1.55;
            margin: 0.35rem 0 0.8rem 0;
            max-width: 46rem;
          }
          .bridge-quote {
            border-left: 3px solid #0f3d3e;
            margin: 0.2rem 0 0.9rem 0;
            padding: 0.15rem 0 0.15rem 0.9rem;
            color: #1c1915;
            line-height: 1.5;
          }
          div[data-testid="stAlert"] {border-radius: 12px;}
          div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 14px;
            background: #fffdf8;
          }
          .stTextArea textarea, .stTextInput input {
            border-radius: 10px !important;
            background: #fffdf8 !important;
          }
          button[kind="primary"], [data-testid="stBaseButton-primary"] {
            background-color: #0f3d3e !important;
            color: #f6f3ec !important;
            border: none !important;
            min-height: 3.1rem;
            border-radius: 12px !important;
            font-weight: 680;
          }
          button[kind="secondary"], [data-testid="stBaseButton-secondary"] {
            border-radius: 10px !important;
            min-height: 2.7rem;
          }
          h2, h3 {letter-spacing: -0.02em;}
          @media (max-width: 720px) {
            .bridge-hero h1 {font-size: 2.2rem;}
            .bridge-lede {font-size: 1.05rem;}
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
