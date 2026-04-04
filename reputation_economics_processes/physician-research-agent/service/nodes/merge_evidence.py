"""
Evidence merge node — structures Perplexity prose and consolidates all sources.

Two responsibilities:
  1. Structuring step: convert each raw PerplexityResearchResult into typed
     intermediate dicts (structured_perplexity). This is a Claude API call
     using the structuring.md prompt template. Never skip this step — raw
     Perplexity prose must not go directly to dossier assembly.

  2. Evidence merge: combine NPPES, PubMed, Semantic Scholar, and structured
     Perplexity outputs into merged_evidence (field_path → list[EvidenceItem]).

Source priority (when sources conflict):
  1. Structured API (NPPES, PubMed) beats synthesized (Perplexity)
  2. Official institutional source beats third-party directory
  3. Recent source beats older when titles/roles differ

Implemented in Step 11.
"""

from __future__ import annotations

from service.state import ReasoningState


def merge_evidence_node(state: ReasoningState) -> dict:
    """
    Reads:  state["request"], state["identity_resolution"]
    Writes: state["structured_perplexity"], state["merged_evidence"],
            state["run_issues"], state["decision_log"]

    Implemented in Step 11.
    """
    raise NotImplementedError("Implemented in Step 11")
