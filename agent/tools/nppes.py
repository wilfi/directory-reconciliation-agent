"""NPPES registry lookup interface (skeleton).

In production this calls the public NPPES API and caches responses in Postgres.
Here it is stubbed so readers can see the contract the agent tools rely on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NppesRecord:
    npi: str
    first_name: str | None = None
    last_name: str | None = None
    is_deactivated: bool = False
    practice_locations: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class NppesLookup:
    found: bool
    record: NppesRecord | None = None
    raw: dict[str, Any] = field(default_factory=dict)


def lookup_npi(npi: str) -> NppesLookup:
    """Look up an NPI in NPPES.

    Skeleton stub — replace with a real HTTP client + cache in a full build.
    """
    raise NotImplementedError(
        "Wire to https://npiregistry.cms.hhs.gov/api/ (see full project for cache + backoff)"
    )
