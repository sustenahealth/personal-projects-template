"""
Pydantic v2 models for the Physician Research Agent.

These are the source of truth for all data structures. The JSON schemas in
schemas/ are derived from these models and must remain in sync.

Contract invariants:
- Every non-null dossier field carries at least one EvidenceItem.
- Null fields use NullSemantic values — never bare None without a reason.
- Relationship records are separate from the dossier body so they can be
  exported independently to PDA custom_data CSV.
- The /synthesize contract is versioned from day one (contract_version 0.1.0).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums — controlled vocabularies
# ---------------------------------------------------------------------------


class ConfidenceTier(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class ExtractionMethod(str, Enum):
    structured_api = "structured_api"
    perplexity = "perplexity"
    llm_synthesis = "llm_synthesis"
    manual = "manual"


class RelationshipType(str, Enum):
    published_with = "PublishedWith"
    strong_published_with = "StrongPublishedWith"
    institution_overlap = "InstitutionOverlap"


class RunStatus(str, Enum):
    success = "success"
    success_with_warnings = "success_with_warnings"
    needs_follow_up = "needs_follow_up"
    failed = "failed"


class DossierQualityTier(str, Enum):
    good = "Good"
    usable_but_incomplete = "UsableButIncomplete"
    failed = "Failed"


class IdentityResolutionState(str, Enum):
    resolved_confidently = "resolved_confidently"
    resolved_with_warning = "resolved_with_warning"
    unresolved = "unresolved"


class NullSemantic(str, Enum):
    """
    Explicit null reasons — use instead of bare None for any field that was
    actively researched and came back empty or uncertain.

    not_researched — this field was not attempted in this run (e.g. optional
                     prompt skipped due to graceful degradation)
    not_found      — field was researched but no evidence was located
    ambiguous      — evidence exists but is contradictory or unresolvable
    not_applicable — field is structurally inapplicable to this physician
    """

    not_researched = "not_researched"
    not_found = "not_found"
    ambiguous = "ambiguous"
    not_applicable = "not_applicable"


class RunIssueType(str, Enum):
    ambiguity = "ambiguity"
    missing_data = "missing_data"
    source_failure = "source_failure"
    conflict = "conflict"
    low_confidence = "low_confidence"


class IssueSeverity(str, Enum):
    blocking = "blocking"
    warning = "warning"
    info = "info"


class ReviewStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


# ---------------------------------------------------------------------------
# Shared building blocks
# ---------------------------------------------------------------------------


class EvidenceItem(BaseModel):
    """
    Provenance attached to a dossier field. Every non-null dossier field must
    carry at least one EvidenceItem.
    """

    field_name: str = Field(..., description="The dossier field this evidence supports")
    value: str = Field(..., description="The raw value as extracted from the source")
    source_type: str = Field(..., description="e.g. 'pubmed', 'nppes', 'perplexity', 'institutional_page'")
    source_url: str | None = None
    source_title: str | None = None
    evidence_snippet: str | None = Field(None, description="Verbatim snippet from the source supporting the value")
    extraction_method: ExtractionMethod
    confidence: ConfidenceTier
    retrieved_at: datetime | None = None
    review_status: ReviewStatus = ReviewStatus.pending


class RunIssue(BaseModel):
    """A logged problem from a single run."""

    issue_type: RunIssueType
    severity: IssueSeverity
    message: str
    source_step: str = Field(..., description="Which graph node or process raised this issue")
    field_affected: str | None = None
    blocking: bool = False


# ---------------------------------------------------------------------------
# Input models — what n8n sends to /synthesize
# ---------------------------------------------------------------------------


class PhysicianResearchInput(BaseModel):
    """Physician identity and search context as received from n8n."""

    run_id: str
    name: str
    institution: str | None = None
    specialty: str | None = None
    npi: str | None = Field(None, description="Preferred NPI if already known")


class NPPESCandidate(BaseModel):
    """A candidate NPPES record returned by the n8n NPPES lookup."""

    npi: str
    first_name: str
    last_name: str
    full_name: str
    specialty: str | None = None
    state: str | None = None
    city: str | None = None
    taxonomy_description: str | None = None
    is_preferred: bool = Field(False, description="Set by n8n if deterministic match found")


class PublicationRecord(BaseModel):
    """A publication record from PubMed or Semantic Scholar."""

    pmid: str | None = None
    semantic_scholar_id: str | None = None
    title: str
    authors: list[str]
    year: int | None = None
    journal: str | None = None
    doi: str | None = None
    source: Literal["pubmed", "semantic_scholar"]
    co_author_npi_candidates: list[str] = Field(
        default_factory=list,
        description="NPIs of co-authors who may also be in the physician universe",
    )


class SemanticScholarSummary(BaseModel):
    """Aggregated author-level data from Semantic Scholar."""

    author_id: str | None = None
    paper_count: int | None = None
    citation_count: int | None = None
    h_index: int | None = None
    research_topics: list[str] = Field(default_factory=list)
    top_co_authors: list[str] = Field(default_factory=list)
    retrieval_success: bool = True
    failure_reason: str | None = None


class PerplexityResearchResult(BaseModel):
    """
    Raw response from one Perplexity prompt in the prompt pack.

    The structuring node converts raw_response into typed intermediate objects
    before dossier synthesis. Never pass raw_response directly to assembly.
    """

    prompt_key: Literal["role", "training", "awards_committees", "presence"]
    raw_response: str | None = None
    citations: list[str] = Field(default_factory=list)
    retrieval_success: bool = True
    failure_reason: str | None = None


class SourceMetadata(BaseModel):
    """Provenance and counts for each upstream source call."""

    nppes_queried_at: datetime | None = None
    pubmed_queried_at: datetime | None = None
    semantic_scholar_queried_at: datetime | None = None
    perplexity_queried_at: datetime | None = None
    nppes_record_count: int = 0
    pubmed_record_count: int = 0
    semantic_scholar_record_count: int = 0


class RunContext(BaseModel):
    """Campaign and client context passed through from n8n."""

    requested_by: str | None = None
    client_hospital: str | None = None
    service_line: str | None = None
    campaign_cycle: str | None = Field(None, description="e.g. '2026-2027'")


class LangGraphRequest(BaseModel):
    """
    The full payload n8n posts to POST /synthesize.
    Versioned from day one — downstream consumers must check contract_version.
    """

    contract_version: str = "0.1.0"
    input: PhysicianResearchInput
    identity_candidates: list[NPPESCandidate] = Field(default_factory=list)
    publication_records: list[PublicationRecord] = Field(default_factory=list)
    semantic_scholar_summary: SemanticScholarSummary | None = None
    perplexity_results: list[PerplexityResearchResult] = Field(default_factory=list)
    source_metadata: SourceMetadata = Field(default_factory=SourceMetadata)
    run_context: RunContext = Field(default_factory=RunContext)


# ---------------------------------------------------------------------------
# Dossier body — structured physician profile
# ---------------------------------------------------------------------------


class IdentityResolution(BaseModel):
    """Output of the disambiguate node."""

    state: IdentityResolutionState
    preferred_npi: str | None = None
    preferred_name: str | None = None
    preferred_specialty: str | None = None
    preferred_institution: str | None = None
    decision_log: str = Field(..., description="Human-readable rationale for the resolution decision")
    evidence: list[EvidenceItem] = Field(default_factory=list)


class CurrentRole(BaseModel):
    title: str | None = None
    institution: str | None = None
    department: str | None = None
    division: str | None = None
    null_reason: NullSemantic | None = Field(
        None, description="Set if role could not be determined"
    )
    evidence: list[EvidenceItem] = Field(default_factory=list)


class EducationRecord(BaseModel):
    institution: str
    degree: str | None = None
    program: str | None = None
    years: str | None = Field(None, description="e.g. '2000-2004'")
    evidence: list[EvidenceItem] = Field(default_factory=list)


class TrainingRecord(BaseModel):
    institution: str
    training_type: str = Field(..., description="residency | fellowship | advanced_training")
    specialty: str | None = None
    years: str | None = Field(None, description="e.g. '2004-2007'")
    evidence: list[EvidenceItem] = Field(default_factory=list)


class StructuredPublication(BaseModel):
    pmid: str | None = None
    title: str
    authors: list[str]
    year: int | None = None
    journal: str | None = None
    is_candidate_only: bool = Field(
        False,
        description="True if author identity is uncertain — excluded from relationship records",
    )
    evidence: list[EvidenceItem] = Field(default_factory=list)


class CommitteeMembership(BaseModel):
    """
    Committee and society membership is the highest-value desk research category.
    A dossier is not 'Good' unless this section is either populated or explicitly
    marked as a known gap via committees_null_reason.
    """

    organization: str
    committee: str | None = None
    role: str | None = None
    years: str | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)


class Award(BaseModel):
    name: str
    organization: str | None = None
    year: int | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)


class PublicPresence(BaseModel):
    institutional_profile_url: str | None = None
    linkedin_url: str | None = None
    twitter_handle: str | None = None
    media_appearances: list[str] = Field(default_factory=list)
    null_reason: NullSemantic | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)


class PhysicianDossier(BaseModel):
    """
    The structured physician profile produced by the dossier assembly node.

    Null-reason fields must be set whenever the corresponding list is empty —
    the distinction between "not_found" and "not_researched" matters downstream.
    """

    identity: IdentityResolution
    current_role: CurrentRole = Field(default_factory=CurrentRole)

    education: list[EducationRecord] = Field(default_factory=list)
    education_null_reason: NullSemantic | None = None

    training: list[TrainingRecord] = Field(default_factory=list)
    training_null_reason: NullSemantic | None = None

    publications: list[StructuredPublication] = Field(default_factory=list)
    publications_null_reason: NullSemantic | None = None

    committees_societies: list[CommitteeMembership] = Field(default_factory=list)
    committees_null_reason: NullSemantic | None = Field(
        None,
        description=(
            "MUST be set if committees_societies is empty. "
            "Committee/society membership is mandatory to research — "
            "use not_found if researched but empty, not_researched only if "
            "the awards_committees Perplexity prompt was skipped."
        ),
    )

    awards: list[Award] = Field(default_factory=list)
    awards_null_reason: NullSemantic | None = None

    public_presence: PublicPresence = Field(default_factory=PublicPresence)


# ---------------------------------------------------------------------------
# Relationship records — separate from the dossier body
# ---------------------------------------------------------------------------


class RelationshipRecord(BaseModel):
    """
    A direct relationship between two physicians. V1 emits PublishedWith,
    StrongPublishedWith, and InstitutionOverlap only.

    All records require_review = True until a human approves them for
    durable downstream use in Collaborator Tables.
    """

    relationship_type: RelationshipType
    source_physician_name: str = Field(..., description="The physician being researched")
    source_physician_npi: str | None = None
    target_physician_name: str = Field(..., description="The related physician")
    target_physician_npi: str | None = None
    confidence: ConfidenceTier
    evidence_summary: str = Field(..., description="Human-readable rationale; required — label alone is insufficient")
    publication_count: int | None = Field(None, description="Shared publication count for PublishedWith types")
    shared_institutions: list[str] = Field(default_factory=list, description="For InstitutionOverlap")
    requires_review: bool = True


class PDARelationshipRow(BaseModel):
    """
    Output row matching the curated.custom_data schema consumed by custom_data_etl.
    One RelationshipRecord maps to one or more PDARelationshipRows.
    """

    data_label: str = Field(..., description="e.g. 'PublishedWith_JoelHirschhorn'")
    hospital: str = Field(..., description="Client hospital name")
    service_line: str = Field(..., description="USNWR specialty")
    username: str | None = Field(None, description="Doximity username if known")
    npi: str | None = Field(None, description="Target physician NPI")
    name: str = Field(..., description="Target physician full name")
    data_value: str = Field(..., description="Relationship type or organization name")
    other: str | None = Field(None, description="Evidence summary: publication count, shared committees, etc.")


# ---------------------------------------------------------------------------
# Run metrics and response envelope
# ---------------------------------------------------------------------------


class RunMetrics(BaseModel):
    total_duration_seconds: float | None = None
    llm_calls: int = 0
    llm_tokens_used: int = 0
    sources_used: list[str] = Field(default_factory=list)
    publications_found: int = 0
    relationships_extracted: int = 0
    estimated_cost_usd: float | None = None


class LangGraphResponse(BaseModel):
    """
    The full response the LangGraph service returns to n8n.
    Versioned — contract_version must match the request.
    """

    contract_version: str = "0.1.0"
    run_id: str
    run_status: RunStatus
    dossier_quality_tier: DossierQualityTier
    dossier: PhysicianDossier
    relationship_records: list[RelationshipRecord] = Field(default_factory=list)
    pda_relationship_rows: list[PDARelationshipRow] = Field(default_factory=list)
    run_issues: list[RunIssue] = Field(default_factory=list)
    decision_log: list[str] = Field(default_factory=list)
    metrics: RunMetrics = Field(default_factory=RunMetrics)
    created_at: datetime = Field(default_factory=datetime.utcnow)
