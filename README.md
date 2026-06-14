# agent-lens

**Eval + observability for LLM agents.** The production layer you build *around*
any agent: trace-level evaluation, causal failure analysis, cost/latency
dashboards, and CI eval-gates that block regressions before they ship.

> Not another agent framework. agent-lens is the *measurement* harness you wrap
> around the agents you already have — model-agnostic, framework-agnostic,
> 100% free-tier.

---

## Why trace-level eval matters in 2026

Shipping an agent is easy; *knowing it still works after a model bump* is the
hard part. **Evaluation is the #1 weighted skill on the 2026 AI-Engineer
surface** — and the eval techniques most teams reach for were built for
single prompt/response pairs, not agents.

An agent run is a **multi-step trajectory**: plan → call tool → read result →
re-plan → answer. A naive LLM-as-judge that only grades the final answer will
happily pass a run that reached the right answer via the **wrong tools**,
**3x the cost**, or an **unsafe action**. agent-lens grades the *whole
trajectory* — which tools were called, in what order, at what cost, and where
it actually went wrong.

## Architecture

```
        ┌──────────────────────────────────────────────────────────────┐
        │  YOUR AGENT (e.g. claims-auditor)                             │
        │  emits canonical TraceEvents  ── the cross-repo contract ──┐  │
        └───────────────────────────────────────────────────────────│──┘
                                                                     ▼
   ┌──────────┐   TraceEvents   ┌──────────┐   EvalResults   ┌──────────────┐
   │ tracing  │ ───────────────▶│   eval   │ ───────────────▶│   analysis   │
   │ (OTel)   │   build Trace   │ judge +  │  scores/metrics │ causal root- │
   │ capture  │                 │ heuristic│                 │ cause finder │
   └────┬─────┘                 └────┬─────┘                 └──────┬───────┘
        │                            │                              │
        │ spans/metrics              │ EvalReport                   │
        ▼                            ▼                              ▼
   ┌──────────────┐            ┌──────────────┐              ┌──────────────┐
   │  dashboards  │            │   ci gate    │              │  exporters   │
   │ Prometheus / │            │ block merge  │              │ Langfuse /   │
   │ Grafana      │            │ on regression│              │ LangSmith    │
   └──────────────┘            └──────────────┘              └──────────────┘
```

The **`TraceEvent`** schema is the spine: every step of an agent run is one
`TraceEvent`, linked into a trajectory tree (`session_id` / `step_id` /
`parent_step_id`). Everything downstream consumes that contract.

## Features

- **Trace-level evaluation** — tool-call correctness, trajectory scoring,
  multi-turn traces. Not single-call grading.
- **Provider-agnostic LLM-as-judge** — Anthropic directly, or any model via
  OpenRouter / OpenAI-compatible endpoints, with mitigations for the known
  failure modes of judging agent traces.
- **Causal failure analysis** — find the *root-cause* step in a failed session,
  not just the downstream symptom.
- **Cost/latency dashboards** — P50/P95/P99 latency, tokens, and cost per
  session via OpenTelemetry → Prometheus → Grafana.
- **CI eval-gates** — a GitHub Action that fails the build when a model/prompt
  bump regresses your evals.
- **Compatible exports** — ship traces to Langfuse / LangSmith if you're already
  on a hosted platform.

## Quickstart

Install:

```bash
pip install -e ".[dev]"   # or: make install
```

Instrument an agent in ~5 lines (intended ergonomics):

```python
from agent_lens.tracing import trace_session, trace_step
from agent_lens.eval import TrajectoryJudgeEvaluator

with trace_session() as session:
    with trace_step(kind="llm", name="plan"):
        plan = my_llm("which tool answers this?")
    with trace_step(kind="tool", tool_name="search"):
        docs = search(plan.query)

result = TrajectoryJudgeEvaluator(
    model="claude-sonnet-4",
    rubric="Did the agent pick the right tools to answer the question?",
).evaluate(session.trace)

print(result.score, result.passed)
```

The canonical schema already works today — see
[`examples/instrument_toy_agent.py`](examples/instrument_toy_agent.py) for a
runnable demo that builds and prints a `Trace`.

## Metrics / coverage (coming)

| Signal                | Status   |
| --------------------- | -------- |
| `TraceEvent` contract | ✅ concrete + tested |
| Trace-level evaluators| 🚧 Phase 1 |
| Causal analysis       | 🚧 Phase 1 |
| Prometheus/Grafana    | 🚧 Phase 1 |
| CI eval-gate Action   | 🚧 Phase 1 |
| Test coverage badge   | ⏳ pending CI |

## Where it fits

agent-lens is part of a 4-repo **AI Engineer Portfolio Program**. It is the
**measurement layer for the flagship `claims-auditor`**, which emits the
`TraceEvent`s this library consumes.

- [claims-auditor](https://github.com/MarcosRos002/claims-auditor) — flagship, measured by this repo
- [agent-lens](https://github.com/MarcosRos002/agent-lens) — you are here
- [fine-tune-lab](https://github.com/MarcosRos002/fine-tune-lab) — LoRA/distillation
- [portfolio](https://github.com/MarcosRos002/portfolio) — website

## License

MIT — see [LICENSE](LICENSE).
