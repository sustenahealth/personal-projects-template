"""
FastAPI entrypoint for the Physician Research Agent service.

Endpoints:
  GET  /health      — liveness check
  POST /synthesize  — accepts a LangGraphRequest from n8n, returns LangGraphResponse

The /synthesize implementation is a mock until the LangGraph graph is wired
in Steps 10–14. The mock returns a stub response so the full request/response
contract can be validated end-to-end before reasoning logic is built.
"""

from __future__ import annotations

from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from service.config import settings
from service.models import (
    CurrentRole,
    DossierQualityTier,
    IdentityResolution,
    IdentityResolutionState,
    LangGraphRequest,
    LangGraphResponse,
    NullSemantic,
    PhysicianDossier,
    PublicPresence,
    RunMetrics,
    RunStatus,
)
from service.utils.logging import get_logger

log = get_logger(__name__)

app = FastAPI(
    title="Physician Research Agent",
    description=(
        "LangGraph synthesis service for physician desk research dossiers. "
        "Accepts pre-fetched evidence from n8n and returns a structured dossier "
        "with relationship records and run issues."
    ),
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "version": "0.1.0",
        "model": settings.model_name,
    }


# ---------------------------------------------------------------------------
# Synthesize
# ---------------------------------------------------------------------------


@app.post("/synthesize", response_model=LangGraphResponse)
async def synthesize(request: LangGraphRequest) -> LangGraphResponse:
    """
    Core endpoint. Receives evidence payload from n8n and returns a structured
    physician dossier.

    Current state: MOCK — returns a stub response with unresolved identity and
    not_researched null reasons. Full reasoning graph is wired in Steps 10–14.
    """
    log.info(
        "synthesize request received",
        extra={
            "run_id": request.input.run_id,
            "physician": request.input.name,
            "institution": request.input.institution,
            "identity_candidates": len(request.identity_candidates),
            "publications": len(request.publication_records),
            "perplexity_results": len(request.perplexity_results),
        },
    )

    # --- MOCK IMPLEMENTATION ---
    # Replace this block when the LangGraph graph is wired (Step 10+).
    mock_identity = IdentityResolution(
        state=IdentityResolutionState.unresolved,
        decision_log="Mock: disambiguation node not yet implemented (Step 10)",
    )
    mock_dossier = PhysicianDossier(
        identity=mock_identity,
        current_role=CurrentRole(null_reason=NullSemantic.not_researched),
        education_null_reason=NullSemantic.not_researched,
        training_null_reason=NullSemantic.not_researched,
        publications_null_reason=NullSemantic.not_researched,
        committees_null_reason=NullSemantic.not_researched,
        awards_null_reason=NullSemantic.not_researched,
        public_presence=PublicPresence(null_reason=NullSemantic.not_researched),
    )

    return LangGraphResponse(
        run_id=request.input.run_id,
        run_status=RunStatus.needs_follow_up,
        dossier_quality_tier=DossierQualityTier.failed,
        dossier=mock_dossier,
        decision_log=["Mock response — LangGraph graph not yet wired (Steps 10-14)"],
        metrics=RunMetrics(),
        created_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    uvicorn.run(
        "service.app:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=True,
    )
