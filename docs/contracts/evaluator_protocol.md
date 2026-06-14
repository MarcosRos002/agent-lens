# Contract: the Evaluator Protocol

Source of truth: [`src/agent_lens/eval/base.py`](../../src/agent_lens/eval/base.py).

An **evaluator** is anything that scores a whole `Trace` and returns an
`EvalResult`. Operating on the full `Trace` (not a single call) is what makes
trajectory and tool-call evaluation possible.

## Interface

```python
@runtime_checkable
class Evaluator(Protocol):
    name: str
    def evaluate(self, trace: Trace) -> EvalResult: ...
```

### Rules

1. **Input is a whole `Trace`.** Evaluators must reason over the step tree, not
   just the final answer.
2. **Pure w.r.t. the trace.** No mutation of the input; deterministic given the
   same trace + config (LLM judges pin `temperature=0` and record the judge
   `model`/`model_version` in `metadata` for reproducibility).
3. **Inject expensive resources at construction.** LLM clients, rubrics, and
   thresholds are constructor args; `evaluate()` does the work.
4. **`name` is stable and namespaced**, e.g. `heuristic:tool_call_correctness`,
   `llm_judge:trajectory`. The CI eval-gate keys off these names.
5. **Always set `score` (∈ [0,1]) and `passed`.** `passed` is the boolean the
   eval-gate consumes; `metrics[]` carries the breakdown; `rationale` is kept for
   failure analysis.

## Built-in evaluators (Phase 1)

| Name                               | Kind      | What it scores |
| ---------------------------------- | --------- | -------------- |
| `heuristic:tool_call_correctness`  | heuristic | Did the agent call the expected tools (optionally in order)? Deterministic, no model calls — runs first in CI. |
| `llm_judge:trajectory`             | LLM-judge | Rubric score over the full trajectory: right tools, sensible order, safe, cost-aware. Provider-agnostic; supports self-consistency sampling. |

## Why naive LLM-as-judge fails on agent traces

Documented in [`src/agent_lens/eval/llm_judge.py`](../../src/agent_lens/eval/llm_judge.py):

- **Final-answer bias** — grading only the last message passes runs that reached
  the right answer via wrong/expensive/unsafe steps.
- **Context overflow** — long traces bury the decisive step; judges lose the plot.
- **Position / verbosity / self-preference bias** inflates scores.
- **Non-determinism** — a single sample is noisy.

**Mitigations agent-lens is built around:** score the trajectory tree with a
step-aware rubric; decompose into per-step judgments; pin judge model +
`temperature=0` and record its version; optional self-consistency (k samples,
median) for high-stakes evals.
