# Contract: `EvalResult`, `Metric`, `EvalReport`

Source of truth:
[`src/agent_lens/schema/eval_result.py`](../../src/agent_lens/schema/eval_result.py).
This is the **output** contract — what evaluators produce and what dashboards +
the CI eval-gate consume.

## `Metric`

A single named measurement over a trace or step.

| Field       | Type              | Description |
| ----------- | ----------------- | ----------- |
| `name`      | `str`             | Metric id, e.g. `tool_call_correctness`, `cost_usd`. |
| `value`     | `float`           | The measurement. |
| `direction` | `MetricDirection` | `higher_is_better` (default) or `lower_is_better`. **Needed for regression gating** so the gate knows which way a drop hurts. |
| `unit`      | `str \| null`     | `ratio` · `usd` · `ms` · `tokens`. |
| `metadata`  | `dict`            | Free-form. |

## `EvalResult`

Result of running **one evaluator** over **one trace** (or step).

| Field       | Type             | Description |
| ----------- | ---------------- | ----------- |
| `evaluator` | `str`            | Evaluator name, e.g. `llm_judge:trajectory`. |
| `session_id`| `str`            | Trace this result is about. |
| `step_id`   | `str \| null`    | Set when the result scopes a single step. |
| `score`     | `float [0,1]`    | Normalized headline score. |
| `passed`    | `bool`           | Threshold decision the **CI eval-gate** reads. |
| `metrics`   | `list[Metric]`   | Breakdown behind the score. |
| `rationale` | `str \| null`    | Judge/heuristic explanation — kept for failure analysis. |
| `metadata`  | `dict`           | Free-form (judge model/version, thresholds, …). |

## `EvalReport`

Aggregate of many `EvalResult`s — what a CI run or dashboard refresh emits.

| Field      | Type               | Description |
| ---------- | ------------------ | ----------- |
| `suite`    | `str`              | Suite name, e.g. `claims-auditor-nightly`. |
| `results`  | `list[EvalResult]` | The results. |
| `metadata` | `dict`             | Free-form. |
| `pass_rate`| `float` (computed) | Fraction of results with `passed == True`. |

## How the CI eval-gate uses this

The gate compares a **current** `EvalReport` against a stored **baseline**
report. It fails the build when `pass_rate` (or a gated metric, respecting its
`direction`) regresses beyond `tolerance`. See
[`src/agent_lens/ci/gate.py`](../../src/agent_lens/ci/gate.py) and
`docs/modules/ci.md`.
