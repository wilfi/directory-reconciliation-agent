"""Tools the Strands agent may call during reconciliation.

Each function is a tool the model can choose. In the full project these are
decorated with Strands `@tool` and backed by NPPES / address / name helpers.
This skeleton keeps the same names and contracts so the article maps cleanly.
"""

from __future__ import annotations

from typing import Any

# In the full project:
#   from strands import tool
#   @tool(context=True)
#   def check_npi_format(...): ...


def check_npi_format(npi: str) -> dict[str, Any]:
    """Validate that an NPI is 10 digits with a correct Luhn check digit.

    Call this before looking up the NPI registry.
    """
    digits = npi.isdigit() and len(npi) == 10
    return {"npi": npi, "valid": digits}  # full project also runs Luhn


def lookup_npi_registry(npi: str) -> dict[str, Any]:
    """Look up a provider in the authoritative NPPES NPI Registry.

    Returns name, deactivation status, and practice locations.
    """
    # Full project: agent.tools.nppes.lookup_npi(session, npi) + api_cache
    return {
        "found": False,
        "npi": npi,
        "hint": "Implement via agent.tools.nppes.lookup_npi",
    }


def validate_practice_address(
    line1: str,
    city: str,
    state: str,
    zip_code: str,
    line2: str = "",
) -> dict[str, Any]:
    """Normalize and validate a US practice address."""
    return {
        "input": {"line1": line1, "line2": line2, "city": city, "state": state, "zip": zip_code},
        "normalized": True,
        "hint": "Full project uses Google Address Validation or local USPS-style normalize",
    }


def match_provider_name(
    directory_first: str,
    directory_last: str,
    nppes_first: str,
    nppes_last: str,
) -> dict[str, Any]:
    """Compare directory name to NPPES (nicknames / maiden names allowed)."""
    exact = (
        directory_first.strip().upper() == nppes_first.strip().upper()
        and directory_last.strip().upper() == nppes_last.strip().upper()
    )
    return {
        "outcome": "exact" if exact else "different",
        "directory": f"{directory_first} {directory_last}",
        "nppes": f"{nppes_first} {nppes_last}",
    }


def compare_practice_addresses(
    directory_line1: str,
    directory_city: str,
    directory_state: str,
    nppes_locations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare directory address to NPPES practice locations."""
    return {
        "best_match": "unknown",
        "directory": {
            "line1": directory_line1,
            "city": directory_city,
            "state": directory_state,
        },
        "nppes_location_count": len(nppes_locations),
        "hint": "Full project returns exact / same_city / different with evidence",
    }


# Registered tool list passed into the Strands Agent in llm.py
RECONCILIATION_TOOLS = [
    check_npi_format,
    lookup_npi_registry,
    validate_practice_address,
    match_provider_name,
    compare_practice_addresses,
]
