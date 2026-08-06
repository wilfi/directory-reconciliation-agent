# Provider directories are messy. An AI shouldn’t guess anyway.

Provider directories look simple from the outside: a clinician name, an office address, a phone number, an NPI.

Underneath, they are often messy. The same person can appear more than once. An old practice location can linger. Names don’t always match the official registry exactly. Some identifiers are inactive. The file is large enough that manual review doesn’t scale cleanly.

That creates a tempting but weak design:

> Ask a language model whether the listing is correct.

A model can answer fluently. Fluency is not evidence. In a directory workflow, a confident wrong answer is worse than no answer.

So the useful pattern is not “generate an opinion.”  
It is “run an investigation protocol.”

This article walks through that protocol. The companion repo is a **skeleton** — enough code to connect the dots, not a full production clone.

---

## 1. What the agent does

Health plans are required to keep provider directories accurate, yet CMS audits routinely find a large share of entries wrong (moved practices, wrong addresses, deactivated NPIs).

The agent automates the first verification pass: for each directory record it gathers evidence from authoritative sources and issues a structured, evidence-cited verdict:

- `VERIFIED`
- `STALE`
- `DEACTIVATED`
- `NEEDS_HUMAN_REVIEW`

```text
CMS-style directory row (messy)
        │
        ▼
Reconciliation agent ──► tool loop (model chooses next action)
        │                  tools:
        │                    • check_npi_format
        │                    • lookup_npi_registry (NPPES)
        │                    • validate_practice_address
        │                    • match_provider_name
        │                    • compare_practice_addresses
        ▼
Verdict {status, confidence, rule_path, evidence}
```

A thin adapter stores the result and applies policy (see confidence floor below).

**Code map**

- [`agent/reconcile.py`](agent/reconcile.py) — adapter + policy
- [`agent/tools/llm.py`](agent/tools/llm.py) — agent loop entry
- [`agent/tools/agent_tools.py`](agent/tools/agent_tools.py) — tools the model may call

---

## 2. Built with AWS Strands

The investigation is owned by a **Strands** agent: a model-driven loop where the model chooses tools, reads results, and continues until it can return a structured verdict.

Strands is an open-source agents SDK (originally released by AWS) designed for exactly this shape of work — tools + model + structured outcomes.

- Docs: [https://strandsagents.com/](https://strandsagents.com/)
- Intro: [Introducing Strands Agents (AWS Open Source Blog)](https://aws.amazon.com/blogs/opensource/introducing-strands-agents-an-open-source-ai-agents-sdk/)

In code, the important pieces are:

1. A **system prompt** that defines the job and verdict meanings  
2. A **tool list** the model may call  
3. A **structured output** schema (`VerdictOutput`) for the final decision  

```python
# Shape from agent/tools/llm.py
agent = Agent(
    model=...,
    system_prompt=SYSTEM_PROMPT,
    tools=RECONCILIATION_TOOLS,
)
result = agent(prompt, structured_output=VerdictOutput)
```

The model is not asked to invent the registry. It is asked to **use tools**, then judge.

**Code map**

- [`agent/tools/llm.py`](agent/tools/llm.py) — `SYSTEM_PROMPT`, `VerdictOutput`, `run_reconciliation_agent`
- [`agent/tools/nppes.py`](agent/tools/nppes.py) — NPPES lookup contract (stubbed in the skeleton)

---

## 3. Messy provider data → verdicts

Public CMS-style directory data is full of almosts: suite numbers, suppressed address lines, multiple locations per NPI, and rows that look related but aren’t.

Below are real-shaped examples from a working run (public NPIs). Full fixtures live in [`samples/`](samples/).

### Same clinician, two addresses

**Luisa Skoble** (`1003820432`)

| Directory address | Verdict | Why |
|---|---|---|
| 593 Eddy St, Providence, RI | `VERIFIED` (0.99) | Name + NPPES practice location match |
| 45 Wells St Suite 104, Westerly, RI | `STALE` (0.95) | Same person; Westerly not in NPPES locations |

**Raymond Hinson** (`1003821828`)

| Directory address | Verdict | Why |
|---|---|---|
| 111 E 210th St, Bronx, NY | `VERIFIED` (0.95) | Match despite ZIP formatting noise |
| 12 N 7th Ave, Mount Vernon, NY | `STALE` (0.95) | Active NPI/name; address not in NPPES |

### Conflict that should not auto-resolve

**Cindy Queliza** on NPI `1003582156` at Manhasset addresses → `NEEDS_HUMAN_REVIEW`

NPPES for that NPI resolves to a different last name (Abelido) and a Great Neck location. That is not a safe automatic `STALE` or `VERIFIED` — it needs a human.

### Clean happy path

**Kapedjanie Bois** (`1003049883`) at 154 Waterman St Suite 1B, Providence → `VERIFIED` (1.0) after the full tool trail (NPI → NPPES → name → address).

**Code map**

- [`samples/messy_inputs.json`](samples/messy_inputs.json)
- [`samples/verdict_outputs.json`](samples/verdict_outputs.json)

---

## 4. How confidence is measured (LLM-as-judge) + eval harness

### Confidence is not a Python formula

The structured verdict includes `confidence` from `0.0` to `1.0`. That number is **reported by the model** after it has seen tool results — LLM-as-judge over evidence, not:

```text
confidence = 0.4 * name_score + 0.6 * address_score
```

So it can vary by model quality. Small local models are often poorly calibrated; stronger hosted models are usually better, but still not a hard sensor reading.

### Confidence floor (fail closed)

Policy in [`agent/reconcile.py`](agent/reconcile.py):

```python
LLM_CONFIDENCE_FLOOR = 0.6

if result.confidence < LLM_CONFIDENCE_FLOOR:
    # keep the model's reason/evidence, but do not trust the label
    return NEEDS_HUMAN_REVIEW  # rule_path = strands:low_confidence
```

Example from the fixtures: a conflict case with confidence `0.15` is stored as `NEEDS_HUMAN_REVIEW` with `strands:low_confidence` — even if the narrative already pointed at a problem.

### Eval harness (the real quality check)

Self-reported confidence is not enough. A **golden set** of labeled listings is scored offline:

- escalation rate  
- accuracy when decisive  
- recall for important labels like `STALE`  
- a gate that fails the run if recall drops too far  

The skeleton includes a tiny sample harness:

```bash
python -m evals.run
```

**Code map**

- [`agent/reconcile.py`](agent/reconcile.py) — confidence floor  
- [`agent/tools/llm.py`](agent/tools/llm.py) — `VerdictOutput.confidence`  
- [`evals/run.py`](evals/run.py) — scoring + gate  
- [`evals/golden.sample.jsonl`](evals/golden.sample.jsonl) — labeled sample rows  

---

## 5. The code as a reference map

This repository is intentionally incomplete as a product. It is complete as a **map**:

```text
ARTICLE.md                 ← you are here
README.md                  ← how sections map to files
agent/reconcile.py         ← verdict policy + confidence floor
agent/tools/llm.py         ← Strands agent + system prompt + structured verdict
agent/tools/agent_tools.py ← tools the model may call
agent/tools/nppes.py       ← registry lookup contract
evals/                     ← golden-sample scoring idea
samples/                   ← messy inputs + real-shaped verdict outputs
core/models.py             ← Provider / Verdict shapes
```

Connect the dots in this order:

1. Read the diagram in section 1  
2. Open `llm.py` + `agent_tools.py` for the Strands loop  
3. Read `samples/` for messy reality  
4. Open `reconcile.py` for the confidence floor  
5. Run `python -m evals.run` for the measurement idea  

Deploying a full stack (API, batch jobs, dashboards) is a later chapter. The protocol comes first:

**Investigate with tools. Decide in a fixed format. Fail closed when unsure. Measure against labels.**

---

### Data note

Examples use publicly available CMS-style provider directory fields and the public NPPES registry. This is an independent learning/prototype pattern, not a CMS system or endorsement.
