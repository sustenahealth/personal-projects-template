"""Structured logging via rich. Use get_logger() everywhere — no print() calls."""

from __future__ import annotations

import logging

from rich.logging import RichHandler


def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)],
    )
    return logging.getLogger(name)
