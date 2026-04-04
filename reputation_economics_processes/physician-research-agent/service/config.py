"""
Single source of truth for all configuration and environment variables.

Usage:
    from service.config import settings

Service startup fails immediately with a clear message if any required key
is missing. Optional keys fall back to documented defaults.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console

_console = Console(stderr=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Required ──────────────────────────────────────────────────────────────
    anthropic_api_key: str = Field(..., description="Anthropic API key (ANTHROPIC_API_KEY)")
    perplexity_api_key: str = Field(..., description="Perplexity API key (PERPLEXITY_API_KEY)")

    # ── Recommended (degrade gracefully without them) ─────────────────────────
    ncbi_api_key: str | None = Field(
        None,
        description="PubMed E-utilities key — 3 req/s without, 10 req/s with (NCBI_API_KEY)",
    )
    semantic_scholar_api_key: str | None = Field(
        None,
        description="Semantic Scholar API key — higher rate limits (SEMANTIC_SCHOLAR_API_KEY)",
    )

    # ── Model ─────────────────────────────────────────────────────────────────
    model_name: str = Field(
        "claude-sonnet-4-6",
        description="Claude model ID used for all LLM calls (MODEL_NAME)",
    )

    # ── Service ───────────────────────────────────────────────────────────────
    service_host: str = Field("0.0.0.0", description="FastAPI bind host (SERVICE_HOST)")
    service_port: int = Field(8000, description="FastAPI bind port (SERVICE_PORT)")
    log_level: str = Field("INFO", description="Logging level (LOG_LEVEL)")

    # ── Paths ─────────────────────────────────────────────────────────────────
    output_dir: Path = Field(
        Path("output"),
        description="Directory for run artifact output — created on startup (OUTPUT_DIR)",
    )
    prompts_dir: Path = Field(
        Path("service/prompts"),
        description="Directory containing prompt template .md files (PROMPTS_DIR)",
    )

    # ── Timeouts ──────────────────────────────────────────────────────────────
    perplexity_timeout: int = Field(
        30, description="Perplexity API timeout in seconds (PERPLEXITY_TIMEOUT)"
    )
    external_api_timeout: int = Field(
        15, description="Default timeout for NPPES/PubMed/Semantic Scholar (EXTERNAL_API_TIMEOUT)"
    )

    # ── LLM ───────────────────────────────────────────────────────────────────
    max_llm_retries: int = Field(3, description="Max retries for LLM API calls")

    # ── Optional ──────────────────────────────────────────────────────────────
    benchmark_case: str | None = Field(
        None,
        description="Named benchmark fixture to run at startup (BENCHMARK_CASE)",
    )


def _load_settings() -> Settings:
    """Load settings, exiting with a clear message on missing required keys."""
    try:
        s = Settings()  # type: ignore[call-arg]
    except Exception as exc:
        _console.print(f"[bold red]Configuration error:[/bold red] {exc}")
        _console.print(
            "Copy [cyan].env.example[/cyan] to [cyan].env[/cyan] and fill in required values."
        )
        sys.exit(1)

    s.output_dir.mkdir(parents=True, exist_ok=True)

    if not s.ncbi_api_key:
        _console.print(
            "[yellow]Warning:[/yellow] NCBI_API_KEY not set — PubMed rate limit is 3 req/s."
        )
    if not s.semantic_scholar_api_key:
        _console.print(
            "[yellow]Warning:[/yellow] SEMANTIC_SCHOLAR_API_KEY not set — lower rate limits apply."
        )

    return s


settings: Settings = _load_settings()
