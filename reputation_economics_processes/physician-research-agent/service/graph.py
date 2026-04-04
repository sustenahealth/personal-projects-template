"""
LangGraph reasoning graph definition.

The graph runs four nodes in sequence:
  disambiguate → merge_evidence → extract_relationships → assemble_dossier

Node implementations are added in Steps 10–14. This stub builds a valid
StateGraph so the service starts without import errors.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from service.state import ReasoningState


def build_graph() -> StateGraph:
    """
    Construct and return the compiled reasoning graph.

    Uncomment node wiring as each step is implemented.
    """
    graph = StateGraph(ReasoningState)

    # Step 10: disambiguation node
    # from service.nodes.disambiguate import disambiguate_node
    # graph.add_node("disambiguate", disambiguate_node)
    # graph.set_entry_point("disambiguate")

    # Step 11: evidence merge + Perplexity structuring
    # from service.nodes.merge_evidence import merge_evidence_node
    # graph.add_node("merge_evidence", merge_evidence_node)
    # graph.add_edge("disambiguate", "merge_evidence")

    # Step 12: relationship extraction
    # from service.nodes.extract_relationships import extract_relationships_node
    # graph.add_node("extract_relationships", extract_relationships_node)
    # graph.add_edge("merge_evidence", "extract_relationships")

    # Step 13: dossier assembly
    # from service.nodes.assemble_dossier import assemble_dossier_node
    # graph.add_node("assemble_dossier", assemble_dossier_node)
    # graph.add_edge("extract_relationships", "assemble_dossier")
    # graph.add_edge("assemble_dossier", END)

    return graph
