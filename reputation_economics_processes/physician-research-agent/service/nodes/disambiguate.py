"""
Disambiguation node — resolves physician identity from NPPES candidates.

Produces IdentityResolution with one of three states:
  resolved_confidently  — one candidate strongly matches name + specialty + geography
  resolved_with_warning — best candidate plausible but not definitive
  unresolved            — multiple plausible candidates or no match

If identity is unresolved, the run continues but:
  - high-confidence relationship output is suppressed
  - relationships are emitted as low-confidence candidates only
  - a run_issue is added with severity=warning

Implemented in Step 10.
"""

from __future__ import annotations

from service.state import ReasoningState


def disambiguate_node(state: ReasoningState) -> dict:
    """
    Reads:  state["request"] — input physician + NPPES candidates
    Writes: state["identity_resolution"], state["run_issues"], state["decision_log"]

    Implemented in Step 10.
    """
    raise NotImplementedError("Implemented in Step 10")
