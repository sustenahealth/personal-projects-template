"""
Confidence tier assignment logic.

Rule of thumb (from CLAUDE.md):
  High   — structured API or official institutional source (PubMed PMID, NPPES, faculty page)
  Medium — strong secondary source or multi-source synthesis aligned
  Low    — inferred or weakly supported; requires reviewer confirmation before durable use

Implemented in Step 11 (merge_evidence node).
"""

from __future__ import annotations

from service.models import ConfidenceTier


def assign_confidence(source_type: str, has_multiple_sources: bool = False) -> ConfidenceTier:
    """
    Assign a confidence tier based on source type.
    Multi-source agreement can upgrade Medium → High.

    Implemented in Step 11.
    """
    raise NotImplementedError("Implemented in Step 11 (merge_evidence node)")
