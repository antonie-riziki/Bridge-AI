"""Validated models for sources, claims, and analysis results."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_SOURCE_CHARS = 8000
MAX_LABEL_CHARS = 120
MAX_SUMMARY_CHARS = 2000


class Language(str, Enum):
    ENGLISH = "en"
    KISWAHILI = "sw"
    SHENG = "sheng"


class ReadingLevel(str, Enum):
    SIMPLE = "simple"
    STANDARD = "standard"


class ResolutionStatus(str, Enum):
    CONSISTENT = "CONSISTENT"
    CONFLICTING = "CONFLICTING"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    ANALYSIS_FAILED = "ANALYSIS_FAILED"


class ProviderMode(str, Enum):
    LIVE = "live"
    DEMO = "demo"


class ClaimCategory(str, Enum):
    DATE = "date"
    TIME = "time"
    LOCATION = "location"
    AMOUNT = "amount"
    NAME = "name"
    EVENT = "event"
    OTHER = "other"


class SourceDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1, max_length=32)
    label: str = Field(min_length=1, max_length=MAX_LABEL_CHARS)
    text: str = Field(min_length=1, max_length=MAX_SOURCE_CHARS)

    @field_validator("label", "text")
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned


class ExtractedClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1, max_length=32)
    claim_text: str = Field(min_length=1, max_length=500)
    source_id: str = Field(min_length=1, max_length=32)
    source_label: str = Field(min_length=1, max_length=MAX_LABEL_CHARS)
    category: ClaimCategory
    excerpt: str = Field(min_length=1, max_length=500)


class EvidenceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_id: str = Field(min_length=1, max_length=32)
    source_id: str = Field(min_length=1, max_length=32)
    source_label: str = Field(min_length=1, max_length=MAX_LABEL_CHARS)
    excerpt: str = Field(min_length=1, max_length=500)
    note: str = Field(default="", max_length=300)


class ClaimAgreement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=500)
    claim_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(min_length=2)


class ClaimConflict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=800)
    topic: str = Field(min_length=1, max_length=40)
    values_by_source: dict[str, str] = Field(min_length=2)
    claim_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def values_must_differ(self) -> "ClaimConflict":
        unique = {value.strip() for value in self.values_by_source.values() if value.strip()}
        if len(self.values_by_source) < 2 or len(unique) < 2:
            raise ValueError("a conflict needs at least two different values")
        return self


class EvidenceComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ResolutionStatus
    agreements: list[ClaimAgreement] = Field(default_factory=list)
    conflicts: list[ClaimConflict] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    claims: list[ExtractedClaim] = Field(default_factory=list)
    evidence_references: list[EvidenceReference] = Field(default_factory=list)
    limitations: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def status_matches_findings(self) -> "EvidenceComparison":
        if self.conflicts and self.status != ResolutionStatus.CONFLICTING:
            raise ValueError("conflicts require CONFLICTING status")
        if self.status == ResolutionStatus.CONFLICTING and not self.conflicts:
            raise ValueError("CONFLICTING requires a conflict")
        if self.status == ResolutionStatus.CONSISTENT and not self.agreements:
            raise ValueError("CONSISTENT requires an agreement")
        if self.status == ResolutionStatus.CONSISTENT and self.conflicts:
            raise ValueError("CONSISTENT cannot include conflicts")
        return self


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_status: ResolutionStatus
    concise_summary: str = Field(min_length=1, max_length=MAX_SUMMARY_CHARS)
    detected_agreements: list[ClaimAgreement] = Field(default_factory=list)
    detected_conflicts: list[ClaimConflict] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    claims: list[ExtractedClaim] = Field(default_factory=list)
    evidence_references: list[EvidenceReference] = Field(default_factory=list)
    recommended_next_step: str = Field(min_length=1, max_length=1000)
    response_language: Language
    reading_level: ReadingLevel
    limitations: list[str] = Field(min_length=1)
    provider_mode: ProviderMode

    @model_validator(mode="after")
    def status_matches_findings(self) -> "AnalysisResult":
        failed = self.overall_status == ResolutionStatus.ANALYSIS_FAILED
        if failed and (self.detected_conflicts or self.detected_agreements or self.claims):
            raise ValueError("a failed analysis cannot include findings")
        if self.detected_conflicts and self.overall_status != ResolutionStatus.CONFLICTING:
            raise ValueError("conflicts require CONFLICTING status")
        if self.overall_status == ResolutionStatus.CONFLICTING and not self.detected_conflicts:
            raise ValueError("CONFLICTING requires a conflict")
        if self.overall_status == ResolutionStatus.CONSISTENT and not self.detected_agreements:
            raise ValueError("CONSISTENT requires an agreement")
        return self


class ModelExcerpt(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source_id: str = Field(min_length=1, max_length=32)
    excerpt: str = Field(min_length=1, max_length=500)


class ModelSemanticConflict(BaseModel):
    model_config = ConfigDict(extra="ignore")

    summary: str = Field(min_length=1, max_length=500)
    topic: str = Field(min_length=1, max_length=40)
    excerpts: list[ModelExcerpt] = Field(min_length=2)


class ModelNarrative(BaseModel):
    """The only model payload BridgeAI accepts. Extra keys are ignored."""

    model_config = ConfigDict(extra="ignore")

    concise_summary: str = Field(min_length=1, max_length=MAX_SUMMARY_CHARS)
    recommended_next_step: str = Field(min_length=1, max_length=1000)
    semantic_conflicts: list[ModelSemanticConflict] = Field(default_factory=list)
    extra_limitations: list[str] = Field(default_factory=list)

    @field_validator("extra_limitations", mode="before")
    @classmethod
    def limitations_as_list(cls, value: object) -> object:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [value]
        return value

    @field_validator("semantic_conflicts", mode="before")
    @classmethod
    def conflicts_as_list(cls, value: object) -> object:
        if value is None:
            return []
        return value
