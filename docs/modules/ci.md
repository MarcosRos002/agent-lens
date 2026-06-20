# Module: `ci`

**Status:** implemented (Phase 1). `EvalGate` + CLI (`run_gate` / `python -m
agent_lens.ci.gate`) pinned by `tests/test_ci_gate.py`. Two GitHub Actions wired:
`.github/workflows/ci.yml` (lint + tests) and `.github/workflows/eval-gate.yml`
(runs `examples/run_eval_suite.py` → gates against `eval/baseline_report.json`).
Gating is **per-evaluator + per-metric, direction-aware, relative tolerance**
(not the global `pass_rate`, which is confounded when the evaluator set changes).

## Purpose

The **eval-gate**: a runner (wired into a GitHub Action) that runs an eval suite
over a set of traces and **fails the build when evals regress** — e.g. when a
model/prompt version bump drops trajectory score.

## Interface (intended)

```python
from agent_lens.ci import EvalGate, GateOutcome

outcome = EvalGate(tolerance=0.02).check(current_report, baseline_report)
# GateOutcome.PASS / GateOutcome.FAIL  -> CI exit code
```

A `.github/workflows/eval-gate.yml` (Phase 1) invokes this on PRs, loading the
baseline `EvalReport` from the target branch.

## Dependencies

- `agent_lens.schema` (`EvalReport`).
- `agent_lens.eval` to produce the current report.
- GitHub Actions (free for public repos).

## How to test

- Pass when current ≥ baseline within tolerance.
- Fail when a gated metric regresses beyond tolerance, respecting each metric's
  `direction` (lower-is-better metrics like cost/latency must not silently pass).
- Edge cases: empty/missing baseline (first run), new evaluators added.

## Senior concerns

- **Flaky evals = flaky CI.** LLM-judge non-determinism must be controlled
  (temperature 0, self-consistency, or heuristic-only gates) before gating merges.
- Baseline management: where it's stored, how it's updated on intentional changes.
- Clear failure output: which evaluator/metric regressed, by how much.
