"""
LangGraph reasoning state — the typed state dict threaded through the graph.

Each node reads from state and returns a partial dict of updated keys.
The graph merges updates automatically.

Node responsibilities:
  disambiguate        → sets identity_resolution
  merge_evidence      → sets structured_perplexity, merged_evidence
  extract_relations   → sets relationship_records
  assemble_dossier    → sets dossier, dossier_quality_tier, run_status

run_issues and decision_log accumulate across all nodes.
"""

from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict

from service.models import (
    DossierQualityTier,
    IdentityResolution,
    LangGraphRequest,
    PhysicianDossier,
    RelationshipRecord,
    RunIssue,
    RunMetrics,
    RunStatus,
)


class ReasoningState(TypedDict, total=False):
    # ── Input ────────────────────────────────────────────────────────────────
    # Set at graph entry from the /synthesize request. Never mutated by nodes.
    request: LangGraphRequest

    # ── Node 1: disambiguate ─────────────────────────────────────────────────
    identity_resolution: IdentityResolution | None

    # ── Node 2: merge_evidence ───────────────────────────────────────────────
    # structured_perplexity: prompt_key → typed intermediate dict extracted
    # from raw Perplexity prose by the structuring step.
    # Do not pass raw Perplexity responses to dossier assembly.
    structured_perplexity: dict[str, Any]

    # merged_evidence: field_path → list of EvidenceItem dicts.
    # Used by assembly node to attach provenance to dossier fields.
    merged_evidence: dict[str, list[dict[str, Any]]]

    # ── Node 3: extract_relationships ────────────────────────────────────────
    relationship_records: list[RelationshipRecord]

    # ── Node 4: assemble_dossier ─────────────────────────────────────────────
    dossier: PhysicianDossier | None
    dossier_quality_tier: DossierQualityTier | None

    # ── Accumulated across all nodes ─────────────────────────────────────────
    run_issues: list[RunIssue]
    decision_log: list[str]
    run_status: RunStatus | None
    metrics: RunMetrics
