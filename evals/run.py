"""Tiny eval harness: score predicted verdicts against a golden sample.

Full projects use ~110 labeled rows + live/cached tool calls. This skeleton
shows the scoring idea the article describes:

- compare predicted status to expected_status
- escalations (NEEDS_HUMAN_REVIEW) are tracked separately
- gate on STALE recall (example threshold)

Usage:
    python -m evals.run
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

GOLDEN = Path(__file__).parent / "golden.sample.jsonl"
# Example regression gate from the full project
RECALL_GATES = {"STALE": 0.8}


def load_golden() -> list[dict]:
    return [json.loads(line) for line in GOLDEN.read_text().splitlines() if line.strip()]


def score(entries: list[dict]) -> dict:
    """Score rows that already include predicted_status (demo / offline).

    In the full harness, predicted_status comes from running reconcile() on each
    golden NPI against a database + tool cache.
    """
    confusion: dict[str, Counter] = defaultdict(Counter)
    for e in entries:
        confusion[e["expected_status"]][e["predicted_status"]] += 1

    total = len(entries)
    escalations = sum(1 for e in entries if e["predicted_status"] == "NEEDS_HUMAN_REVIEW")
    statuses = sorted({e["expected_status"] for e in entries} | {e["predicted_status"] for e in entries})
    per_status = {}
    for status in statuses:
        actual = sum(confusion[status].values())
        predicted = sum(confusion[exp][status] for exp in confusion)
        correct = confusion[status][status]
        per_status[status] = {
            "actual": actual,
            "predicted": predicted,
            "precision": (correct / predicted) if predicted else None,
            "recall": (correct / actual) if actual else None,
        }

    decided = [e for e in entries if e["predicted_status"] != "NEEDS_HUMAN_REVIEW"]
    decided_correct = sum(1 for e in decided if e["predicted_status"] == e["expected_status"])

    return {
        "total": total,
        "escalation_rate": escalations / total if total else 0.0,
        "accuracy_when_decisive": (decided_correct / len(decided)) if decided else None,
        "per_status": per_status,
        "confusion": {exp: dict(row) for exp, row in confusion.items()},
    }


def main() -> None:
    entries = load_golden()
    report = score(entries)
    print(f"golden records:         {report['total']}")
    print(f"escalation rate:        {report['escalation_rate']:.1%}")
    acc = report["accuracy_when_decisive"]
    print(f"accuracy when decisive: {acc:.1%}" if acc is not None else "accuracy when decisive: n/a")
    print("\nper-status:")
    for status, m in report["per_status"].items():
        prec = f"{m['precision']:.2f}" if m["precision"] is not None else "-"
        rec = f"{m['recall']:.2f}" if m["recall"] is not None else "-"
        print(f"  {status:<22} actual={m['actual']:<3} pred={m['predicted']:<3} P={prec} R={rec}")

    failures = []
    for status, threshold in RECALL_GATES.items():
        recall = report["per_status"].get(status, {}).get("recall")
        if recall is not None and recall < threshold:
            failures.append(f"{status} recall {recall:.2f} < gate {threshold}")
    if failures:
        print("\nEVAL GATE FAILED:", "; ".join(failures))
        raise SystemExit(1)
    print("\neval gate passed")


if __name__ == "__main__":
    main()
