"""Strands agent that owns the reconciliation tool loop.

Reference for the article section on AWS Strands:
  https://strandsagents.com/
  https://aws.amazon.com/blogs/opensource/introducing-strands-agents-an-open-source-ai-agents-sdk/

The model chooses which tools to call, then returns a structured verdict.
Confidence on that verdict is model-judged (LLM-as-judge over tool evidence),
not a hand-written Python score.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from agent.tools.agent_tools import RECONCILIATION_TOOLS
from core.models import Provider


class LlmUnavailable(Exception):
    pass


@dataclass
class Adjudication:
    status: str
    confidence: float
    reason: str
    raw: dict
    model: str
    tool_calls: list[str] = field(default_factory=list)
    debug: dict[str, Any] = field(default_factory=dict)


class VerdictOutput(BaseModel):
    """Final reconciliation verdict after using tools."""

    status: str = Field(
        description="One of: VERIFIED, STALE, DEACTIVATED, NEEDS_HUMAN_REVIEW"
    )
    confidence: float = Field(
        description="Confidence in the status, 0.0-1.0 (model self-report)",
        ge=0.0,
        le=1.0,
    )
    reason: str = Field(description="One sentence citing the decisive evidence from tools")


SYSTEM_PROMPT = """You are a provider-directory reconciliation agent.

Given one health-plan directory entry, investigate whether it is still accurate \
by using your tools. You decide which tools to call and in what order.

Typical investigation:
1. check_npi_format — skip registry lookup if the NPI is structurally invalid.
2. lookup_npi_registry — authoritative NPPES record (name, deactivation, locations).
3. match_provider_name — compare directory name to NPPES (nicknames/maiden names OK).
4. validate_practice_address and/or compare_practice_addresses — compare directory \
address to NPPES practice locations.

Verdict meanings:
- VERIFIED: same person at a matching practice location (formatting / suite omission OK).
- STALE: same person, but directory address does not match any NPPES practice location.
- DEACTIVATED: NPPES shows the NPI is deactivated and not reactivated.
- NEEDS_HUMAN_REVIEW: conflicting or thin evidence; do not guess.

Use tools before deciding. When finished, return the structured verdict."""


def _provider_prompt(provider: Provider) -> str:
    payload = {
        "npi": provider.npi,
        "first_name": provider.first_name,
        "last_name": provider.last_name,
        "address_line_1": provider.address_line_1,
        "address_line_2": provider.address_line_2,
        "city": provider.city,
        "state": provider.state,
        "zip": provider.zip5,
    }
    return (
        "Reconcile this provider directory entry. Use tools to investigate, "
        "then return a structured verdict.\n\n"
        + json.dumps(payload, indent=2)
    )


def run_reconciliation_agent(provider: Provider) -> Adjudication:
    """Run the Strands tool-loop agent for one provider row.

    Skeleton shape (full project wires Ollama or Bedrock):

        from strands import Agent
        agent = Agent(
            model=_build_model(),
            system_prompt=SYSTEM_PROMPT,
            tools=RECONCILIATION_TOOLS,
        )
        result = agent(_provider_prompt(provider), structured_output=VerdictOutput)

    Returns an Adjudication with status + confidence reported by the model.
    """
    _ = (provider, RECONCILIATION_TOOLS, SYSTEM_PROMPT, _provider_prompt)
    raise LlmUnavailable(
        "Skeleton only — see ARTICLE.md and wire Strands Agent + model provider here"
    )
