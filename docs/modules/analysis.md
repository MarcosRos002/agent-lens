# Module: `analysis`

**Status:** implemented (Phase 1). `find_root_cause(trace)` walks the
`parent_step_id` tree and returns the originating failure (the earliest error with
no failed ancestor), not a downstream symptom; `None` if the trace didn't fail.
Pinned by `tests/test_causal.py`.

## Purpose

Causal failure analysis over multi-step sessions: given a failed `Trace`,
identify the **root-cause step** — distinguishing the originating failure from
its downstream symptoms by walking the `parent_step_id` tree.

## Interface (intended)

```python
from agent_lens.analysis import find_root_cause

culprit = find_root_cause(trace)   # -> TraceEvent | None  (None if no failure)
```

Later: cohort analysis across many traces to surface recurring failure patterns.

## Dependencies

- `agent_lens.schema` only (reads `Trace`, returns a `TraceEvent`). No model
  calls required for the structural analysis; an optional LLM pass can summarize
  *why*.

## How to test

- Synthetic traces with a known root cause + propagated downstream errors;
  assert the originating step is returned, not the symptom.
- Non-failing traces return `None`.
- Branching trajectories (multiple children) resolve correctly.

## Senior concerns

- **Causal vs. correlational** — the first error in time isn't always the root
  cause; use the tree, not just timestamps.
- Keep the structural pass deterministic and free; reserve LLM use for
  human-readable explanations.
- Make output actionable: point at a specific `step_id` + rationale.
