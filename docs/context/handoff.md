# Handoff

## Where we are

**Phase 1 started — observability + first evaluator built.**
- `metrics.py`: `compute_trace_metrics(trace) -> TraceMetrics` (latency P50/P95
  via nearest-rank, total cost/tokens, error rate, per-step-kind breakdown) +
  `metrics_as_schema()` for dashboards. The `TraceEvent` contract is confirmed
  against what `claims-auditor` actually emits (rules TOOL step + classifier LLM
  step with `pass_used`/`escalated` metadata).
- `eval/heuristic.py`: `ToolCallCorrectnessEvaluator` implemented (trace-level,
  no LLM) — satisfies the `Evaluator` Protocol.
- Pinned by `tests/test_metrics.py` + `tests/test_heuristic_eval.py`. 16 tests pass.
- `ci/gate.py`: **CI eval-gate implemented** — `EvalGate` (direction-aware,
  per-evaluator/per-metric, relative tolerance) + CLI; `.github/workflows/ci.yml`
  (lint+tests) and `eval-gate.yml` (suite → gate vs `eval/baseline_report.json`);
  `examples/run_eval_suite.py`. Pinned by `tests/test_ci_gate.py`. **25 tests pass.**
- `eval/llm_judge.py`: **LLM-as-judge trajectory evaluator implemented** —
  injected `JudgeModel`, structured/validated `JudgeVerdict` with a bounded
  re-prompt, self-consistency via median over `samples`, records judge
  `model`/`provider` for reproducibility. Offline-testable. Pinned by
  `tests/test_llm_judge.py`. **32 tests pass.**
- `analysis/causal.py`: **`find_root_cause` implemented** — walks the
  `parent_step_id` tree, returns the originating failure (not the symptom).
- `dashboards/prometheus.py`: **`PrometheusExporter` implemented** — latency
  histogram + cost/tokens/steps/errors counters (isolated registry), `expose()`;
  Grafana dashboard JSON at `dashboards/grafana/agent_lens.json`.
- Pinned by `tests/test_causal.py` + `tests/test_dashboards.py`. **43 tests pass.**
- `tracing/capture.py`: **`trace_session` + `trace_step` implemented** — instrument
  an agent into a canonical `Trace` (contextvar session/parent linkage, OTel-friendly,
  `Step.record_output/record_model/record_input`). Pinned by `tests/test_tracing.py`.
- `exporters/`: **`LangfuseExporter.to_observations` + `LangSmithExporter.to_runs`
  implemented** — map the canonical Trace onto each platform; `export()` lazily pushes
  via the SDK. Pinned by `tests/test_exporters.py`.
- **54 tests pass.** agent-lens now spans the full loop: capture → eval (heuristic +
  LLM-judge) → metrics/dashboards → causal analysis → CI gate → export.
- **Remaining:** a real `JudgeModel` adapter (Anthropic/OpenRouter, temperature=0)
  for live judging; everything else is offline-complete.

## Phase 0 baseline (still valid)

The repo was scaffolded for a fresh Claude Code session:

- Directory structure under `src/agent_lens/` (schema, tracing, eval, analysis,
  dashboards, ci, exporters) + `tests/`, `examples/`, `docs/`.
- **Concrete, tested `TraceEvent` contract** in `src/agent_lens/schema/`
  (`trace.py`, `eval_result.py`). This is the only non-stub code — it's the
  cross-repo contract.
- All other modules are stubs with real signatures + docstrings (`...` bodies).
- Full docs: `CLAUDE.md`, `README.md`, `docs/architecture.md`,
  `docs/contracts/*`, `docs/adr/0001-stack-and-scope.md`, `docs/orchestration.md`,
  `docs/modules/*`.
- Packaging (`pyproject.toml`, `Makefile`), ruff + pytest config.
- `examples/instrument_toy_agent.py` builds + prints a demo `Trace` today.

## Verify the scaffold

```bash
make install
make test          # schema contract tests pass
make lint
python examples/instrument_toy_agent.py
```

## Next steps (in order)

1. **Finalize the `TraceEvent` schema** in `docs/contracts/trace_event.md` —
   it's the cross-repo contract with `claims-auditor`. Confirm the field set
   against what the flagship will actually emit, then freeze `SCHEMA_VERSION`.
   *This blocks everything else.*
2. **Build `tracing` + `eval` in parallel worktrees** (see
   `docs/orchestration.md`). These two unblock the end-to-end demo and CI.
3. Then fan out `analysis`, `dashboards`, `exporters`; land `ci` (eval-gate)
   last, once a real `eval` exists to gate against.
4. Wire the GitHub Action for the eval-gate and a Grafana dashboard JSON.

## Don't forget

- `schema/` is owned centrally — change it via an ADR + dedicated PR, never
  inside a feature worktree.
- Keep `docs/modules/*.md` in sync as each module gets implemented.
- Coordinate the schema with the `claims-auditor` repo (it's the producer).
