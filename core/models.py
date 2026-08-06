"""Slim domain models for the teaching skeleton.

In the full system these map to Postgres tables (providers, verdicts).
Here they are plain dataclasses so the article code stays readable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Provider:
    """One clinician-at-address row from a provider directory."""

    npi: str
    first_name: str | None = None
    last_name: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state: str | None = None
    zip5: str | None = None
    npi_valid: bool = True


@dataclass
class Verdict:
    """Structured reconciliation outcome for one provider row."""

    npi: str
    status: str  # VERIFIED | STALE | DEACTIVATED | NEEDS_HUMAN_REVIEW
    confidence: float
    rule_path: str
    evidence: dict[str, Any] = field(default_factory=dict)
    model: str | None = None
