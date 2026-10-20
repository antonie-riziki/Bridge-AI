"""Deterministic comparison of dates, times, places, and amounts.

Source text is treated as data. Nothing in a source can change the status rules.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bridgeai.schemas import (
    ClaimAgreement,
    ClaimCategory,
    ClaimConflict,
    EvidenceComparison,
    EvidenceReference,
    ExtractedClaim,
    ResolutionStatus,
    SourceDocument,
)

MONTHS = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
    "januari": 1,
    "februari": 2,
    "machi": 3,
    "aprili": 4,
    "mei": 5,
    "juni": 6,
    "julai": 7,
    "agosti": 8,
    "septemba": 9,
    "oktoba": 10,
    "novemba": 11,
    "desemba": 12,
}

MONTH_NAMES = (
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)

PLACE_STOP = {
    "from",
    "on",
    "between",
    "and",
    "will",
    "for",
    "with",
    "to",
    "free",
    "doors",
    "open",
    "kutoka",
    "saa",
    "kuanzia",
    "mpaka",
}

DATE_RE = re.compile(
    r"""
    \b(?P<iy>\d{4})-(?P<im>\d{2})-(?P<id>\d{2})\b
    |
    \b(?P<dd>\d{1,2})(?:st|nd|rd|th)?\s+(?P<dm>[A-Za-z]{3,12}),?\s+(?P<dy>\d{4})\b
    |
    \b(?P<mmn>[A-Za-z]{3,12})\s+(?P<md>\d{1,2})(?:st|nd|rd|th)?,?\s+(?P<my>\d{4})\b
    |
    \b(?P<n1>\d{1,2})[/-](?P<n2>\d{1,2})[/-](?P<ny>\d{4})\b
    """,
    re.IGNORECASE | re.VERBOSE,
)
TIME_RE = re.compile(
    r"\b(?P<h>\d{1,2}):(?P<minute>\d{2})\s*(?P<ap>a\.?m\.?|p\.?m\.?)?\b"
    r"|\b(?P<h12>\d{1,2})\s*(?P<ap12>a\.?m\.?|p\.?m\.?)\b",
    re.IGNORECASE,
)
PLACE_RE = re.compile(
    r"\b(?:at|in|katika|kwenye)\s+(?:the\s+)?(?P<place>[A-Za-z][A-Za-z]+(?:\s+[A-Za-z]+){0,5})",
    re.IGNORECASE,
)
AMOUNT_RE = re.compile(
    r"\b(?P<cur>ksh|kes|usd)\s?(?P<num>[\d,]+(?:\.\d{1,2})?)\b|\$(?P<usd>[\d,]+(?:\.\d{1,2})?)\b",
    re.IGNORECASE,
)

BASE_LIMITATION = (
    "This check only compares the text you supplied. It does not establish what is true outside those texts."
)
REPETITION_LIMITATION = (
    "A point repeated by more than one source is still not independent proof."
)
DEMO_LIMITATION = (
    "Demo mode uses pattern rules for dates, times, places, and amounts. It does not understand general meaning."
)


class InputError(ValueError):
    """The user's sources cannot be analyzed as entered."""


@dataclass
class Fact:
    topic: str
    category: ClaimCategory
    normalized: str
    display: str
    source_id: str
    source_label: str
    excerpt: str


@dataclass
class Gap:
    kind: str
    topic: str = ""
    source_label: str = ""


@dataclass
class ComparisonBundle:
    comparison: EvidenceComparison
    gaps: list[Gap] = field(default_factory=list)
    ambiguous_numeric_date: bool = False
    demo_rules: bool = True


def validate_source_pairs(pairs: list[tuple[str, str]]) -> list[SourceDocument]:
    """Turn labelled texts into source documents or raise InputError."""
    if len(pairs) < 2:
        raise InputError("Add at least two sources. One text is not enough to compare.")
    if len(pairs) > 4:
        raise InputError("Use no more than four sources at a time.")

    documents: list[SourceDocument] = []
    for index, (label, text) in enumerate(pairs, start=1):
        clean_label = (label or "").strip()
        clean_text = (text or "").strip()
        if not clean_label:
            raise InputError(f"Source {index} needs a short label, such as Clinic announcement.")
        if len(clean_label) > 120:
            raise InputError(f"The label for source {index} is too long. Use 120 characters or fewer.")
        if not clean_text:
            raise InputError(f"{clean_label} is empty. Paste the notice text.")
        if len(clean_text) > 8000:
            raise InputError(
                f"{clean_label} is too long. Use 8000 characters or fewer so the comparison stays readable."
            )
        documents.append(SourceDocument(source_id=f"s{index}", label=clean_label, text=clean_text))
    return documents


def compare_sources(sources: list[SourceDocument]) -> ComparisonBundle:
    """Compare structured values. Instructions inside a source are not followed."""
    if len(sources) < 2:
        raise InputError("Add at least two sources. One text is not enough to compare.")

    facts: list[Fact] = []
    ambiguous = False
    for source in sources:
        found, source_ambiguous = extract_facts(source)
        facts.extend(found)
        ambiguous = ambiguous or source_ambiguous

    claims, references = _claims_from_facts(facts)
    agreements, conflicts, gaps = _match_facts(facts, sources)
    limitations = [BASE_LIMITATION, REPETITION_LIMITATION, DEMO_LIMITATION]
    if ambiguous:
        limitations.append("A numeric date was read as day/month/year, which is the usual order in Kenya.")

    if conflicts:
        status = ResolutionStatus.CONFLICTING
    elif agreements:
        status = ResolutionStatus.CONSISTENT
    else:
        status = ResolutionStatus.INSUFFICIENT_EVIDENCE
        if not any(gap.kind == "no_facts" for gap in gaps):
            gaps.append(Gap(kind="no_shared_fact"))
        gaps.append(Gap(kind="not_verified"))

    if status != ResolutionStatus.INSUFFICIENT_EVIDENCE:
        gaps.append(Gap(kind="not_verified"))

    unresolved = [_gap_english(gap) for gap in gaps]
    comparison = EvidenceComparison(
        status=status,
        agreements=agreements,
        conflicts=conflicts,
        unresolved_questions=unresolved,
        claims=claims,
        evidence_references=references,
        limitations=limitations,
    )
    return ComparisonBundle(
        comparison=comparison,
        gaps=gaps,
        ambiguous_numeric_date=ambiguous,
        demo_rules=True,
    )


def extract_facts(source: SourceDocument) -> tuple[list[Fact], bool]:
    sentences = _sentences(source.text)
    facts: list[Fact] = []
    seen: set[tuple[str, str]] = set()
    ambiguous = False

    def add(topic: str, category: ClaimCategory, normalized: str, display: str, start: int) -> None:
        key = (topic, normalized)
        if key in seen:
            return
        seen.add(key)
        facts.append(
            Fact(
                topic=topic,
                category=category,
                normalized=normalized,
                display=display,
                source_id=source.source_id,
                source_label=source.label,
                excerpt=_excerpt_at(source.text, sentences, start),
            )
        )

    for match in DATE_RE.finditer(source.text):
        parsed = _parse_date(match)
        if parsed is None:
            continue
        normalized, display, was_ambiguous = parsed
        ambiguous = ambiguous or was_ambiguous
        add("date", ClaimCategory.DATE, normalized, display, match.start())

    for match in TIME_RE.finditer(source.text):
        parsed_time = _parse_time(match)
        if parsed_time is None:
            continue
        add("time", ClaimCategory.TIME, parsed_time, parsed_time, match.start())

    for match in PLACE_RE.finditer(source.text):
        place = _clean_place(match.group("place"))
        tokens = [token.casefold() for token in place.split()]
        if len(place) < 3 or not tokens or all(token in MONTHS for token in tokens):
            continue
        add("place", ClaimCategory.LOCATION, place.casefold(), place, match.start())

    for match in AMOUNT_RE.finditer(source.text):
        amount = _parse_amount(match)
        if amount is None:
            continue
        add("amount", ClaimCategory.AMOUNT, amount.casefold(), amount, match.start())

    return facts, ambiguous


def _parse_date(match: re.Match[str]) -> tuple[str, str, bool] | None:
    if match.group("iy"):
        year, month, day = int(match.group("iy")), int(match.group("im")), int(match.group("id"))
        return _date_tuple(year, month, day, ambiguous=False)
    if match.group("dd"):
        month = MONTHS.get(match.group("dm").lower())
        if month is None:
            return None
        return _date_tuple(int(match.group("dy")), month, int(match.group("dd")), ambiguous=False)
    if match.group("md"):
        month = MONTHS.get(match.group("mmn").lower())
        if month is None:
            return None
        return _date_tuple(int(match.group("my")), month, int(match.group("md")), ambiguous=False)
    if match.group("n1"):
        first, second, year = int(match.group("n1")), int(match.group("n2")), int(match.group("ny"))
        if first > 12 and 1 <= second <= 12:
            return _date_tuple(year, second, first, ambiguous=False)
        if second > 12 and 1 <= first <= 12:
            return _date_tuple(year, first, second, ambiguous=True)
        if 1 <= first <= 31 and 1 <= second <= 12:
            return _date_tuple(year, second, first, ambiguous=True)
    return None


def _date_tuple(year: int, month: int, day: int, ambiguous: bool) -> tuple[str, str, bool] | None:
    if not (1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}", f"{day} {MONTH_NAMES[month]} {year}", ambiguous


def _parse_time(match: re.Match[str]) -> str | None:
    if match.group("h"):
        hour = int(match.group("h"))
        minute = int(match.group("minute"))
        ampm = match.group("ap")
    else:
        hour = int(match.group("h12"))
        minute = 0
        ampm = match.group("ap12")
    if minute > 59:
        return None
    if ampm:
        marker = ampm.lower().replace(".", "")
        if hour < 1 or hour > 12:
            return None
        if marker == "pm" and hour < 12:
            hour += 12
        if marker == "am" and hour == 12:
            hour = 0
    elif hour > 23:
        return None
    return f"{hour:02d}:{minute:02d}"


def _parse_amount(match: re.Match[str]) -> str | None:
    if match.group("usd"):
        number = match.group("usd").replace(",", "")
        return f"USD {number}"
    currency = match.group("cur").upper()
    if currency == "KSH":
        currency = "KES"
    number = match.group("num").replace(",", "")
    return f"{currency} {number}"


def _clean_place(raw: str) -> str:
    kept: list[str] = []
    for token in raw.split():
        bare = token.strip(".,;:").lower()
        if bare in PLACE_STOP:
            break
        kept.append(token.strip(".,;:"))
    return " ".join(kept)


def _sentences(text: str) -> list[tuple[int, str]]:
    sentences: list[tuple[int, str]] = []
    start = 0
    for match in re.finditer(r"[.!?]\s+|\n+", text):
        chunk = text[start : match.start() + 1].strip()
        if chunk:
            sentences.append((start, chunk))
        start = match.end()
    tail = text[start:].strip()
    if tail:
        sentences.append((start, tail))
    return sentences or [(0, text.strip())]


def _excerpt_at(text: str, sentences: list[tuple[int, str]], index: int) -> str:
    chosen = text.strip()
    for start, sentence in sentences:
        if start <= index:
            chosen = sentence
    return " ".join(chosen.split())[:500]


def _claims_from_facts(facts: list[Fact]) -> tuple[list[ExtractedClaim], list[EvidenceReference]]:
    claims: list[ExtractedClaim] = []
    references: list[EvidenceReference] = []
    for index, fact in enumerate(facts, start=1):
        claim_id = f"c{index}"
        claims.append(
            ExtractedClaim(
                claim_id=claim_id,
                claim_text=f"{fact.topic.capitalize()} stated: {fact.display}",
                source_id=fact.source_id,
                source_label=fact.source_label,
                category=fact.category,
                excerpt=fact.excerpt,
            )
        )
        references.append(
            EvidenceReference(
                reference_id=f"r{index}",
                source_id=fact.source_id,
                source_label=fact.source_label,
                excerpt=fact.excerpt,
                note=f"{fact.topic}: {fact.display}",
            )
        )
    return claims, references


def _match_facts(
    facts: list[Fact], sources: list[SourceDocument]
) -> tuple[list[ClaimAgreement], list[ClaimConflict], list[Gap]]:
    by_topic: dict[str, list[Fact]] = {}
    for fact in facts:
        by_topic.setdefault(fact.topic, []).append(fact)

    agreements: list[ClaimAgreement] = []
    conflicts: list[ClaimConflict] = []
    gaps: list[Gap] = []
    labels = {source.source_id: source.label for source in sources}

    if not facts:
        gaps.append(Gap(kind="no_facts"))
        return agreements, conflicts, gaps

    for topic, group in by_topic.items():
        per_source: dict[str, list[Fact]] = {}
        for fact in group:
            per_source.setdefault(fact.source_id, []).append(fact)

        if len(per_source) < 2:
            only_id = next(iter(per_source))
            gaps.append(Gap(kind="only_one", topic=topic, source_label=labels.get(only_id, only_id)))
            continue

        value_map: dict[str, str] = {}
        comparable: list[tuple[str, ...]] = []
        for source_id, source_facts in per_source.items():
            unique: list[str] = []
            for fact in source_facts:
                if fact.display not in unique:
                    unique.append(fact.display)
            value_map[source_id] = "; ".join(unique)
            comparable.append(tuple(sorted(unique)))

        claim_ids = [f"c{index}" for index, fact in enumerate(facts, start=1) if fact in group]
        if len(set(comparable)) > 1:
            summary = _conflict_summary(topic, value_map, labels)
            conflicts.append(
                ClaimConflict(
                    summary=summary,
                    topic=topic,
                    values_by_source=value_map,
                    claim_ids=claim_ids,
                )
            )
        else:
            value = next(iter(value_map.values()))
            agreements.append(
                ClaimAgreement(
                    summary=f"Both supplied sources state the same {topic}: {value}.",
                    claim_ids=claim_ids,
                    source_ids=list(value_map.keys()),
                )
            )
    return agreements, conflicts, gaps


def _conflict_summary(topic: str, value_map: dict[str, str], labels: dict[str, str]) -> str:
    parts = [f"{labels.get(source_id, source_id)} states {value}" for source_id, value in value_map.items()]
    joined = ". ".join(parts)
    return f"The {topic} does not match. {joined}."


def _gap_english(gap: Gap) -> str:
    if gap.kind == "no_facts":
        return "Neither source states a date, time, place, or amount that this check can compare."
    if gap.kind == "no_shared_fact":
        return "The sources do not share a date, time, place, or amount."
    if gap.kind == "only_one":
        return f"Only {gap.source_label} states a {gap.topic}. The other text does not."
    if gap.kind == "not_verified":
        return "Nothing in these texts was checked against an independent source."
    return "A needed fact is missing from the supplied text."
