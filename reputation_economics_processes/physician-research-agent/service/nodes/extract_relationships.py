"""
Relationship extraction node — emits direct relationship records only.

V1 relationship types:
  PublishedWith        — 1+ shared publication (structured publication record required)
  StrongPublishedWith  — 3+ shared or repeated recent co-authorship
  InstitutionOverlap   — shared training, employer, or faculty affiliation

Deferred to later versions:
  CommitteeWith, mentor/mentee inference, partnership strength modeling,
  broader social/professional network inference

Rules:
  - No relationship record without evidence_summary (label alone is insufficient)
  - If identity is unresolved, all records emit as confidence=low
  - is_candidate_only publications are excluded from relationship extraction

Implemented in Step 12.
"""

from __future__ import annotations

from service.state import ReasoningState


def extract_relationships_node(state: ReasoningState) -> dict:
    """
    Reads:  state["merged_evidence"], state["identity_resolution"]
    Writes: state["relationship_records"], state["run_issues"], state["decision_log"]

    Implemented in Step 12.
    """
    raise NotImplementedError("Implemented in Step 12")
