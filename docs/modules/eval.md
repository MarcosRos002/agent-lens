# Module: `eval`

**Status:** Phase-0 stub (signatures + the `Evaluator` Protocol are defined).

## Purpose

Score whole agent traces. Houses the `Evaluator` Protocol and the built-in
evaluators: deterministic heuristics (tool-call correctness) and
provider-agnostic LLM-as-judge (trajectory scoring).

## Interface

```python
from agent_lens.eval import (
    Evaluator,                       # Protocol — the extension point
    ToolCallCorrectnessEvaluator,    # heuristic, deterministic, no model calls
    TrajectoryJudgeEvaluator,        # LLM-as-judge over the full trajectory
)

result = TrajectoryJudgeEvaluator(
    model="claude-sonnet-4", provider="anthropic",
    rubric="Did the agent pick the right tools?",
).evaluate(trace)   # -> EvalResult
```

See `docs/contracts/evaluator_protocol.md`.

## Dependencies

- `agent_lens.schema` (`Trace` in, `EvalResult` out).
- `anthropic` and/or `openai` (OpenRouter via the OpenAI-compatible client) for
  the LLM-judge evaluators.

## How to test

- Heuristic evaluators: pure unit tests on crafted `Trace`s (no network).
- LLM-judge: mock the provider client; assert prompt construction, rubric
  injection, score parsing/normalization, and self-consistency aggregation.

## Senior concerns

- **Trace-level, not call-level** — always reason over the step tree.
- Mitigate LLM-judge failure modes (final-answer bias, context overflow,
  position/verbosity/self-preference bias, non-determinism). Pin `temperature=0`,
  record judge `model_version`, support k-sample self-consistency.
- **Cost control** on the free tier: cache judgments, sample, run cheap
  heuristics first and gate the expensive judge behind them.
