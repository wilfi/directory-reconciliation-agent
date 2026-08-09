# Directory reconciliation agent (skeleton)

Teaching skeleton that accompanies [`ARTICLE.md`](ARTICLE.md).

This is **not** a full production system. It is a readable map of the pattern:

messy provider-directory row → Strands tool-loop agent → structured verdict → confidence floor → eval harness.

For a complete implementation (ingest, Postgres, API, AWS deploy), see a fuller project built from the same ideas — this repo stays small on purpose so Medium readers can connect the dots.

## Article → code map

| Article section | Start here |
|---|---|
| What the agent does | [`agent/reconcile.py`](agent/reconcile.py) |
| AWS Strands tool loop | [`agent/tools/llm.py`](agent/tools/llm.py), [`agent/tools/agent_tools.py`](agent/tools/agent_tools.py) |
| Messy samples + verdicts | [`samples/`](samples/) |
| Confidence floor + LLM-as-judge | [`agent/reconcile.py`](agent/reconcile.py) (`LLM_CONFIDENCE_FLOOR`), [`agent/tools/llm.py`](agent/tools/llm.py) (`VerdictOutput`) |
| Eval harness | [`evals/run.py`](evals/run.py), [`evals/golden.sample.jsonl`](evals/golden.sample.jsonl) |

```text
ARTICLE section "what"     →  agent/reconcile.py
ARTICLE section "Strands"  →  agent/tools/llm.py + agent_tools.py
ARTICLE section "samples"  →  samples/*.json
ARTICLE section "confidence/eval" → reconcile.py floor + evals/
```

## Layout

```text
ARTICLE.md                 Medium draft
agent/                     reconciliation protocol (slim)
evals/                     tiny golden-sample scorer
samples/                   messy directory rows + verdict outputs
core/models.py             Provider / Verdict shapes
```

## Run the sample eval

From the repo root (Python 3, no LLM or database needed — predictions are already in the golden file):

```bash
python -m evals.run
```

This scores [`evals/golden.sample.jsonl`](evals/golden.sample.jsonl) and prints escalation rate, accuracy, and `STALE` recall. Useful as a tiny template for a larger labeled set.

## Strands

- https://strandsagents.com/
- https://aws.amazon.com/blogs/opensource/introducing-strands-agents-an-open-source-ai-agents-sdk/

## Data note

Sample NPIs and addresses are from publicly available CMS-style directory / NPPES-shaped runs. Not affiliated with CMS.
