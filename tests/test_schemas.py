"""Schema validation for sources, conflicts, and analysis results."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from bridgeai.schemas import (
    AnalysisResult,
    ClaimConflict,
    EvidenceComparison,
    Language,
    ProviderMode,
    ReadingLevel,
    ResolutionStatus,
    SourceDocument,
)


def test_source_document_strips_and_accepts_text() -> None:
    source = SourceDocument(source_id="s1", label="  Clinic announcement  ", text="  Outreach on 12 March 2026.  ")
    assert source.label == "Clinic announcement"
    assert source.text == "Outreach on 12 March 2026."
    assert source.source_id == "s1"


def test_source_document_rejects_empty_and_overlong_text() -> None:
    with pytest.raises(ValidationError):
        SourceDocument(source_id="s1", label="Notice", text="   ")
    with pytest.raises(ValidationError):
        SourceDocument(source_id="s1", label="Notice", text="x" * 8001)


def test_conflict_requires_different_values() -> None:
    with pytest.raises(ValidationError):
        ClaimConflict(
            summary="Same value",
            topic="date",
            values_by_source={"s1": "12 March 2026", "s2": "12 March 2026"},
        )


def test_consistent_comparison_requires_an_agreement() -> None:
    with pytest.raises(ValidationError):
        EvidenceComparison(
            status=ResolutionStatus.CONSISTENT,
            limitations=["Only the supplied text was checked."],
        )


def test_failed_analysis_cannot_carry_findings() -> None:
    with pytest.raises(ValidationError):
        AnalysisResult(
            overall_status=ResolutionStatus.ANALYSIS_FAILED,
            concise_summary="The live analysis did not return a usable result.",
            detected_conflicts=[
                ClaimConflict(
                    summary="Dates differ",
                    topic="date",
                    values_by_source={"s1": "12 March 2026", "s2": "15 March 2026"},
                )
            ],
            recommended_next_step="Try again.",
            response_language=Language.ENGLISH,
            reading_level=ReadingLevel.SIMPLE,
            limitations=["No analysis was produced."],
            provider_mode=ProviderMode.LIVE,
        )


def test_model_narrative_accepts_a_string_limitation() -> None:
    from bridgeai.schemas import ModelNarrative

    narrative = ModelNarrative.model_validate(
        {
            "concise_summary": "The dates differ.",
            "recommended_next_step": "Ask the organization using a channel you already trust.",
            "extra_limitations": "No external verification was performed.",
            "semantic_conflicts": None,
        }
    )
    assert narrative.extra_limitations == ["No external verification was performed."]
    assert narrative.semantic_conflicts == []


def test_analysis_result_round_trip() -> None:
    result = AnalysisResult(
        overall_status=ResolutionStatus.INSUFFICIENT_EVIDENCE,
        concise_summary="These notices do not establish the answer.",
        unresolved_questions=["No shared date was stated."],
        recommended_next_step="Ask the organization that issued the notice.",
        response_language=Language.KISWAHILI,
        reading_level=ReadingLevel.STANDARD,
        limitations=["Nothing outside the supplied text was checked."],
        provider_mode=ProviderMode.DEMO,
    )
    restored = AnalysisResult.model_validate(result.model_dump(mode="json"))
    assert restored.response_language == Language.KISWAHILI
    assert restored.reading_level == ReadingLevel.STANDARD
    assert restored.provider_mode == ProviderMode.DEMO
