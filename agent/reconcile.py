"""Thin adapter: run the Strands agent, apply a confidence floor, return a verdict.

This is the "fail closed" policy from the article:
the model may propose VERIFIED/STALE, but low confidence becomes human review.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent.tools.llm import Adjudication, LlmUnavailable, run_reconciliation_agent
from core.models import Provider, Verdict

VERIFIED = "VERIFIED"
STALE = "STALE"
DEACTIVATED = "DEACTIVATED"
NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"

# Model-reported confidence below this is not trusted for automatic action.
LLM_CONFIDENCE_FLOOR = 0.6


@dataclass
class ReconcileResult:
    status: str
    confidence: float
    rule_path: str
    evidence: dict[str, Any]
    model: str | None = None


def reconcile(provider: Provider) -> ReconcileResult:
    evidence: dict[str, Any] = {
        "npi": provider.npi,
        "directory_name": f"{provider.first_name or ''} {provider.last_name or ''}".strip(),
        "directory_address": (
            f"{provider.address_line_1 or ''} {provider.address_line_2 or ''}, "
            f"{provider.city}, {provider.state} {provider.zip5 or ''}"
        ).strip(),
    }

    try:
        result: Adjudication = run_reconciliation_agent(provider)
    except LlmUnavailable as exc:
        evidence["llm_error"] = str(exc)[:500]
        evidence["reason"] = "Strands agent unavailable or failed"
        return ReconcileResult(NEEDS_HUMAN_REVIEW, 0.5, "fallback:agent_unavailable", evidence)

    evidence["agent"] = {
        "reason": result.reason,
        "raw": result.raw,
        "tool_calls": result.tool_calls,
    }

    # Confidence is LLM-as-judge over tool evidence — not a Python formula.
    # Soft answers must not silently update a directory.
    if result.confidence < LLM_CONFIDENCE_FLOOR:
        return ReconcileResult(
            NEEDS_HUMAN_REVIEW,
            result.confidence,
            "strands:low_confidence",
            evidence,
            model=result.model,
        )

    return ReconcileResult(
        result.status,
        result.confidence,
        "strands:agent",
        evidence,
        model=result.model,
    )


def to_verdict(provider: Provider, result: ReconcileResult) -> Verdict:
    return Verdict(
        npi=provider.npi,
        status=result.status,
        confidence=result.confidence,
        rule_path=result.rule_path,
        evidence=result.evidence,
        model=result.model,
    )
