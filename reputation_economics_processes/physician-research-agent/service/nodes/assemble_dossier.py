"""
Dossier assembly node — constructs the final PhysicianDossier.

Assembles evidence from merged_evidence into a typed PhysicianDossier, assigns
dossier_quality_tier, and determines run_status.

Quality tier assignment:
  Good                — required fields complete, committee section researched and
                        captured, at least one direct relationship, reviewer spends
                        minutes validating rather than reconstructing
  UsableButIncomplete — core identity and publications correct, one or more
                        non-core sections weak or missing
  Failed              — identity ambiguity unresolved, publication attribution
                        unreliable, or required categories missing without explanation

Run status assignment:
  success              — all required fields populated, no blocking issues
  success_with_warnings — dossier complete but some fields low-confidence or
                           non-critical sources failed
  needs_follow_up      — identity unresolved OR both publication retrieval and
                         identity resolution failed
  failed               — critical failure, no usable output

Required fields for MVP-complete:
  identity, current role/institution, publications/co-author seed set,
  committee/society membership result (positive or explicit gap), education/training,
  at least one direct relationship or explicit absence note.

Implemented in Step 13.
"""

from __future__ import annotations

from service.state import ReasoningState


def assemble_dossier_node(state: ReasoningState) -> dict:
    """
    Reads:  state["merged_evidence"], state["identity_resolution"],
            state["relationship_records"], state["run_issues"]
    Writes: state["dossier"], state["dossier_quality_tier"],
            state["run_status"], state["metrics"]

    Implemented in Step 13.
    """
    raise NotImplementedError("Implemented in Step 13")
