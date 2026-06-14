# Architecture

agent-lens is a pipeline of six modules sitting on top of one shared contract
(the `TraceEvent` schema). Data flows **left to right**: an instrumented agent
emits trace events; we assemble them into a `Trace`; evaluators score the trace;
analysis explains failures; dashboards chart cost/latency; CI gates merges.

## The differentiator: trace-level, not call-level

Most eval tooling grades a single `(prompt, response)` pair. Agents don't work
that way — a run is a **trajectory** of steps (plan → tool → observe → re-plan →
answer). agent-lens treats the **whole trajectory tree** as the unit of
evaluation. That tree is reconstructed from three fields on every event:

- `session_id` — groups all steps of one run into a `Trace`.
- `step_id` — identifies the step.
- `parent_step_id` — points at the step that caused this one (`None` at the root).

Because the trajectory is first-class, evaluators can ask questions a call-level
judge can't: *Were the right tools called, in the right order? Was the final
answer reached cheaply and safely? Which step is the root cause of the failure?*

## Pipeline

```
                        ┌─────────────────────────────┐
                        │   schema/  (THE contract)   │
                        │   TraceEvent · Trace ·       │
                        │   EvalResult · Metric        │
                        └──────────────┬──────────────┘
                                       │ everything imports this
   instrumented agent                  │
   (claims-auditor)                    │
        │ emits                        ▼
        ▼                       ┌─────────────┐
   ┌─────────┐  TraceEvents     │             │
   │ tracing │ ────────────────▶│   Trace     │
   │  (OTel  │  build / assemble │  (one run) │
   │  spans) │                  └──────┬──────┘
   └────┬────┘                         │
        │ spans + raw metrics          │ Trace
        │                              ▼
        │                    ┌───────────────────┐  EvalResult/Report
        │                    │       eval        │ ───────────┐
        │                    │  Evaluator proto: │            │
        │                    │  - llm_judge      │            │
        │                    │  - heuristic      │            │
        │                    │  - trajectory     │            │
        │                    └─────────┬─────────┘            │
        │                              │ Trace + results      │
        │                              ▼                      ▼
        │                    ┌───────────────────┐   ┌───────────────┐
        │                    │     analysis      │   │      ci       │
        │                    │ causal root-cause │   │  eval-gate:   │
        │                    │ over step tree    │   │ fail merge on │
        │                    └───────────────────┘   │  regression   │
        ▼                                            └───────────────┘
   ┌───────────────┐
   │  dashboards   │   ┌──────────────┐
   │ Prometheus →  │   │  exporters   │  Langfuse / LangSmith
   │ Grafana       │   │ (compat out) │  for hosted platforms
   └───────────────┘   └──────────────┘
```

## Module responsibilities

| Module       | Input            | Output                  | Responsibility |
| ------------ | ---------------- | ----------------------- | -------------- |
| `schema`     | —                | pydantic models         | The contract. Concrete + tested. |
| `tracing`    | live agent calls | `TraceEvent` / `Trace`  | OTel-backed capture via decorators / context managers. |
| `eval`       | `Trace`          | `EvalResult` / `EvalReport` | Trajectory + tool-call + LLM-as-judge scoring. |
| `analysis`   | `Trace`          | root-cause `TraceEvent` | Causal failure analysis over the step tree. |
| `dashboards` | `Trace`          | Prometheus metrics      | Cost/latency P50/P95/P99, tokens, errors → Grafana. |
| `ci`         | `EvalReport` × 2 | pass/fail exit code     | Eval-gate: block merges on regression. |
| `exporters`  | `Trace`          | external API calls      | Langfuse/LangSmith-compatible export. |

## Why OpenTelemetry

Capturing traces as OTel spans gives us (a) compatibility with any OTel
collector teams already run, (b) a clean mapping from span → `TraceEvent`, and
(c) free propagation of parent/child relationships via OTel context — which is
exactly the `parent_step_id` linkage our trajectory evaluators need. The Grafana
cost/latency dashboards are fed by a Prometheus exporter derived from the same
spans.

## Where the contract boundary is

The flagship `claims-auditor` depends on **`agent_lens.schema` only**. It emits
`TraceEvent`s; it does not import our evaluators or tracing internals. This keeps
the coupling to a single, versioned wire format (`SCHEMA_VERSION`) and lets both
repos evolve independently. See `docs/contracts/trace_event.md`.
