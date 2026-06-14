"""Causal root-cause analysis across a session's step tree (Phase 0 stub)."""

from __future__ import annotations

from agent_lens.schema import Trace, TraceEvent


def find_root_cause(trace: Trace) -> TraceEvent | None:  # pragma: no cover - Phase 0 stub
    """Return the step most likely the *root* cause of a trace's failure.

    Walks parent_step_id linkage to separate the originating failure from its
    propagated downstream errors. Returns ``None`` if the trace did not fail.
    """
    ...
