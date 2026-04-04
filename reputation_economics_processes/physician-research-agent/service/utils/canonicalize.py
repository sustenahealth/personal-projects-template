"""
Name and NPI canonicalization utilities.

Used by the disambiguate node to normalize physician name variants and
match NPPES candidates against the research input.

Implemented in Step 10 (disambiguate node).
"""

from __future__ import annotations


def normalize_name(name: str) -> str:
    """
    Lowercase, strip credentials, and normalize whitespace.
    e.g. 'Andrew Dauber, MD, MMSc' → 'andrew dauber'

    Implemented in Step 10.
    """
    raise NotImplementedError("Implemented in Step 10 (disambiguate node)")


def names_likely_match(a: str, b: str) -> bool:
    """
    Fuzzy name match — handles 'Andrew J. Dauber' vs 'Andrew Dauber'.

    Implemented in Step 10.
    """
    raise NotImplementedError("Implemented in Step 10 (disambiguate node)")
