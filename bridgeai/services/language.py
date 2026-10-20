"""Language and reading-level wording. Demo mode uses fixed templates, not live translation."""

from __future__ import annotations

from bridgeai.schemas import Language, ReadingLevel, ResolutionStatus
from bridgeai.services.evidence import ComparisonBundle, Gap

TOPIC_WORDS: dict[Language, dict[str, str]] = {
    Language.ENGLISH: {"date": "date", "time": "time", "place": "place", "amount": "amount"},
    Language.KISWAHILI: {"date": "tarehe", "time": "saa", "place": "mahali", "amount": "kiasi"},
    Language.SHENG: {"date": "date", "time": "time", "place": "place", "amount": "kiasi"},
}

STATUS_LABELS: dict[Language, dict[ResolutionStatus, str]] = {
    Language.ENGLISH: {
        ResolutionStatus.CONSISTENT: "Consistent — no material contradiction in the supplied text",
        ResolutionStatus.CONFLICTING: "Conflicting — the supplied texts disagree",
        ResolutionStatus.INSUFFICIENT_EVIDENCE: "Insufficient evidence — these texts do not establish the answer",
        ResolutionStatus.ANALYSIS_FAILED: "Analysis failed — no result was produced",
    },
    Language.KISWAHILI: {
        ResolutionStatus.CONSISTENT: "Inalingana — hakuna mgongano wa wazi katika maandishi uliyopeana",
        ResolutionStatus.CONFLICTING: "Yanapingana — maandishi uliyopeana hayakubaliani",
        ResolutionStatus.INSUFFICIENT_EVIDENCE: "Ushahidi hautoshi — maandishi haya hayathibitishi jibu",
        ResolutionStatus.ANALYSIS_FAILED: "Uchambuzi umeshindwa — hakuna matokeo",
    },
    Language.SHENG: {
        ResolutionStatus.CONSISTENT: "Zinaelewana — hakuna mgongano kwa hii text",
        ResolutionStatus.CONFLICTING: "Hazielewani — hizi text zinasema vitu tofauti",
        ResolutionStatus.INSUFFICIENT_EVIDENCE: "Ushahidi haujatosha — hizi text hazitoi jibu",
        ResolutionStatus.ANALYSIS_FAILED: "Analysis imefail — hakuna result",
    },
}


def instructions(language: Language, reading_level: ReadingLevel) -> str:
    """Instructions for the live model. These are not shown as a translation certificate."""
    language_name = {
        Language.ENGLISH: "English",
        Language.KISWAHILI: "Kiswahili",
        Language.SHENG: "Sheng, kept clear and respectful",
    }[language]
    length = {
        ReadingLevel.SIMPLE: "Use short sentences and familiar words. State the next step plainly.",
        ReadingLevel.STANDARD: "Be concise, and include one sentence of context about the uncertainty.",
    }[reading_level]
    return (
        f"Write concise_summary and recommended_next_step in {language_name}. {length} "
        "Keep every date, time, amount, and proper name exactly as provided in the findings. "
        "Do not add phone numbers, links, or contacts. Do not claim the texts were externally verified. "
        "If a translation is uncertain, say so inside extra_limitations."
    )


def status_label(status: ResolutionStatus, language: Language) -> str:
    return STATUS_LABELS[language][status]


def present(
    bundle: ComparisonBundle,
    language: Language,
    reading_level: ReadingLevel,
    labels_by_id: dict[str, str],
) -> dict[str, object]:
    """Build user-facing wording from structured findings."""
    comparison = bundle.comparison
    agreement_summaries = [
        _localize_agreement(agreement.summary, language) for agreement in comparison.agreements
    ]
    conflict_summaries = [
        _localize_conflict(conflict.topic, conflict.values_by_source, labels_by_id, language)
        for conflict in comparison.conflicts
    ]
    unresolved = [_localize_gap(gap, language) for gap in bundle.gaps]
    summary = _summary(
        comparison.status,
        conflict_summaries,
        agreement_summaries,
        unresolved,
        language,
        reading_level,
    )
    next_step = _next_step(comparison.status, language, reading_level)
    limitations = list(comparison.limitations)
    limitations.extend(_language_limitations(language))
    if reading_level == ReadingLevel.SIMPLE:
        limitations.append("Simple reading mode shortens the explanation. It does not add facts.")
    return {
        "summary": summary,
        "next_step": next_step,
        "limitations": _unique(limitations),
        "unresolved": unresolved,
        "agreement_summaries": agreement_summaries,
        "conflict_summaries": conflict_summaries,
    }


def _localize_agreement(english_summary: str, language: Language) -> str:
    # english form: "Both supplied sources state the same {topic}: {value}."
    prefix = "Both supplied sources state the same "
    if not english_summary.startswith(prefix) or ": " not in english_summary:
        return english_summary
    topic, value = english_summary[len(prefix) :].split(": ", 1)
    value = value.rstrip(".")
    word = TOPIC_WORDS[language].get(topic, topic)
    if language == Language.KISWAHILI:
        return f"Vyanzo vyote viwili vinasema {word} sawa: {value}."
    if language == Language.SHENG:
        return f"Zote mbili zinasema {word} sawa: {value}."
    return f"Both sources state the same {word}: {value}."


def _localize_conflict(
    topic: str,
    values_by_source: dict[str, str],
    labels_by_id: dict[str, str],
    language: Language,
) -> str:
    word = TOPIC_WORDS[language].get(topic, topic)
    pairs = [(labels_by_id.get(source_id, source_id), value) for source_id, value in values_by_source.items()]
    if language == Language.KISWAHILI:
        details = ". ".join(f"{label} inasema {value}" for label, value in pairs)
        return f"{word.capitalize()} haifanani. {details}."
    if language == Language.SHENG:
        details = ". ".join(f"{label} inasema {value}" for label, value in pairs)
        return f"Hii {word} haifanani. {details}."
    details = ". ".join(f"{label} says {value}" for label, value in pairs)
    return f"The {word} does not match. {details}."


def _localize_gap(gap: Gap, language: Language) -> str:
    word = TOPIC_WORDS[language].get(gap.topic, gap.topic)
    if gap.kind == "no_facts":
        return {
            Language.ENGLISH: "Neither source states a date, time, place, or amount that this check can compare.",
            Language.KISWAHILI: "Hakuna chanzo kilichotaja tarehe, saa, mahali, au kiasi ambacho ukaguzi huu unaweza kulinganisha.",
            Language.SHENG: "Hakuna notice iliyoweka date, time, place, ama kiasi ambayo hii check inaweza linganisha.",
        }[language]
    if gap.kind == "no_shared_fact":
        return {
            Language.ENGLISH: "The sources do not share a date, time, place, or amount.",
            Language.KISWAHILI: "Vyanzo hivi havishiriki tarehe, saa, mahali, au kiasi.",
            Language.SHENG: "Hizi notice hazishiriki date, time, place, ama kiasi.",
        }[language]
    if gap.kind == "only_one":
        return {
            Language.ENGLISH: f"Only {gap.source_label} states a {word}. The other text does not.",
            Language.KISWAHILI: f"{gap.source_label} pekee ndiyo inataja {word}. Maandishi mengine hayataji.",
            Language.SHENG: f"{gap.source_label} pekee inataja {word}. Ile nyingine haiko na hiyo.",
        }[language]
    if gap.kind == "not_verified":
        return {
            Language.ENGLISH: "Nothing in these texts was checked against an independent source.",
            Language.KISWAHILI: "Hakuna kitu katika maandishi haya kilichoangaliwa kwa chanzo huru.",
            Language.SHENG: "Hakuna kitu hapa kilicho-check na chanzo ingine.",
        }[language]
    return {
        Language.ENGLISH: "A needed fact is missing from the supplied text.",
        Language.KISWAHILI: "Taarifa inayohitajika haipo katika maandishi uliyopeana.",
        Language.SHENG: "Kitu muhimu kinakosa kwa hii text.",
    }[language]


def _summary(
    status: ResolutionStatus,
    conflicts: list[str],
    agreements: list[str],
    unresolved: list[str],
    language: Language,
    reading_level: ReadingLevel,
) -> str:
    extra = reading_level == ReadingLevel.STANDARD
    if status == ResolutionStatus.CONFLICTING:
        lead = {
            Language.ENGLISH: "These notices do not agree.",
            Language.KISWAHILI: "Matangazo haya hayakubaliani.",
            Language.SHENG: "Hizi notice hazielewani.",
        }[language]
        closing = {
            Language.ENGLISH: "The texts do not show which one is right.",
            Language.KISWAHILI: "Maandishi haya hayatuonyeshi ni lipi sahihi.",
            Language.SHENG: "Hatuna proof ni gani iko sawa.",
        }[language]
        context = {
            Language.ENGLISH: "A difference in the written details is a contradiction in the supplied evidence. It does not show which notice is newer.",
            Language.KISWAHILI: "Tofauti katika maelezo yaliyoandikwa ni mgongano katika ushahidi uliotolewa. Haionyeshi ni tangazo lipi jipya zaidi.",
            Language.SHENG: "Hii tofauti iko kwa text uliyopewa. Haionyeshi ni notice gani ndio latest.",
        }[language]
        parts = [lead, *conflicts, closing]
        if extra:
            parts.append(context)
        return " ".join(parts)

    if status == ResolutionStatus.CONSISTENT:
        lead = {
            Language.ENGLISH: "On the points this check can compare, the notices agree.",
            Language.KISWAHILI: "Katika mambo ambayo ukaguzi huu unaweza kulinganisha, matangazo yanakubaliana.",
            Language.SHENG: "Kwa vitu ambavyo hii check inaweza linganisha, notice zinaelewana.",
        }[language]
        closing = {
            Language.ENGLISH: "Agreement inside these texts is not outside proof.",
            Language.KISWAHILI: "Makubaliano ndani ya maandishi haya si uthibitisho wa nje.",
            Language.SHENG: "Kukubaliana kwa hizi text si proof ya nje.",
        }[language]
        context = {
            Language.ENGLISH: "Use the shared points as a reading of these notices, then confirm them if the decision matters.",
            Language.KISWAHILI: "Tumia mambo yanayofanana kama usomaji wa matangazo haya, kisha uyathibitishe ikiwa uamuzi ni muhimu.",
            Language.SHENG: "Hii ni reading ya hizi notice. Kama uamuzi ni muhimu, confirm tena.",
        }[language]
        parts = [lead, *agreements, closing]
        if extra:
            parts.append(context)
        return " ".join(parts)

    lead = {
        Language.ENGLISH: "These notices do not establish the answer.",
        Language.KISWAHILI: "Matangazo haya hayathibitishi jibu.",
        Language.SHENG: "Hizi notice hazitoi jibu.",
    }[language]
    closing = {
        Language.ENGLISH: "A missing fact is not a confirmed fact.",
        Language.KISWAHILI: "Taarifa iliyokosekana si taarifa iliyothibitishwa.",
        Language.SHENG: "Kitu kinachokosa si kitu kilichothibitishwa.",
    }[language]
    context = {
        Language.ENGLISH: "The check did not find a shared date, time, place, or amount, and it did not treat silence as agreement.",
        Language.KISWAHILI: "Ukaguzi haukuona tarehe, saa, mahali, au kiasi kinachoshirikiwa, na haukuhesabu ukimya kama makubaliano.",
        Language.SHENG: "Check haikuona date, time, place, ama kiasi inayoshare, na haikuchukulia kimya kama agreement.",
    }[language]
    useful = [item for item in unresolved if item][:2]
    parts = [lead, *useful, closing]
    if extra:
        parts.append(context)
    return " ".join(parts)


def _next_step(status: ResolutionStatus, language: Language, reading_level: ReadingLevel) -> str:
    if status == ResolutionStatus.CONFLICTING:
        simple = {
            Language.ENGLISH: (
                "Contact the organization that issued the notices, using a phone number or address you already trust. "
                "Ask which detail is correct. Do not use a contact that appears only inside these unverified texts."
            ),
            Language.KISWAHILI: (
                "Wasiliana na shirika lililotoa matangazo, ukitumia nambari au anwani unayoiamini tayari. "
                "Uliza ni maelezo yapi sahihi. Usitumie mawasiliano yaliyoandikwa ndani ya maandishi haya pekee."
            ),
            Language.SHENG: (
                "Uliza ofisi iliyotoa notice, ukitumia namba ama address unayoijua tayari. "
                "Waulize ni detail gani iko sawa. Usichukue contact kutoka kwa hizi text pekee."
            ),
        }[language]
    elif status == ResolutionStatus.CONSISTENT:
        simple = {
            Language.ENGLISH: (
                "If the decision matters, confirm the shared points with the organization through a channel you already trust. "
                "These notices agree with each other. They were not checked against any other source."
            ),
            Language.KISWAHILI: (
                "Ikiwa uamuzi ni muhimu, thibitisha mambo yanayofanana na shirika kupitia njia unayoiamini tayari. "
                "Matangazo haya yanakubaliana. Hayakuangaliwa kwa chanzo kingine."
            ),
            Language.SHENG: (
                "Kama uamuzi ni muhimu, confirm na ofisi kupitia njia unayoijua tayari. "
                "Hizi notice zinaelewana. Haziku-check na chanzo ingine."
            ),
        }[language]
    else:
        simple = {
            Language.ENGLISH: (
                "Ask the issuing organization, or read a notice you can confirm came from them. "
                "These texts do not establish the fact, so do not fill the gap with a guess."
            ),
            Language.KISWAHILI: (
                "Uliza shirika lililohusika, au soma tangazo unaloweza kuthibitisha kuwa latoka kwao. "
                "Maandishi haya hayathibitishi ukweli, kwa hiyo usijaze pengo kwa kubahatisha."
            ),
            Language.SHENG: (
                "Uliza ofisi husika, ama soma notice unajua imetoka kwao. "
                "Hizi text hazithibitishi kitu, so usijaze gap kwa kubahatisha."
            ),
        }[language]
    if reading_level == ReadingLevel.SIMPLE:
        return simple
    extra = {
        Language.ENGLISH: " This recommendation only restates the check. It does not add facts.",
        Language.KISWAHILI: " Pendekezo hili linasisitiza ukaguzi tu. Haliongezi taarifa mpya.",
        Language.SHENG: " Hii step inarudia check tu. Haiongezi facts mpya.",
    }[language]
    return simple + extra


def _language_limitations(language: Language) -> list[str]:
    if language == Language.ENGLISH:
        return []
    if language == Language.KISWAHILI:
        return [
            "Kiswahili wording in demo mode comes from fixed templates, not a live translation model. It has not been independently validated."
        ]
    return [
        "Sheng wording in this prototype is a fixed best-effort template. It has not been independently validated, and some English words are kept so the meaning stays exact."
    ]


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered
