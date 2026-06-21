"""Causal root-cause analysis across a session's step tree.

Agent failures live in multi-step causal chains, not single calls: a tool errors,
the LLM gets bad data, a downstream step fails. Grading only the *last* error
fixes the symptom, not the cause. ``find_root_cause`` walks the
``parent_step_id`` tree to return the **originating** failure — the earliest error
step that has no failed ancestor. Returns ``None`` when the trace did not fail.
"""

from __future__ import annotations

from agent_lens.schema import StepStatus, Trace, TraceEvent


def find_root_cause(trace: Trace) -> TraceEvent | None:
    """Return the step most likely the *root* cause of the trace's failure."""
    by_id = {e.step_id: e for e in trace.events}
    error_ids = {e.step_id for e in trace.events if e.status is StepStatus.ERROR}
    if not error_ids:
        return None

    def has_failed_ancestor(event: TraceEvent) -> bool:
        parent_id = event.parent_step_id
        while parent_id is not None:
            if parent_id in error_ids:
                return True
            parent = by_id.get(parent_id)
            parent_id = parent.parent_step_id if parent else None
        return False

    # Originating errors = failures whose ancestors did NOT fail (not symptoms).
    originating = [e for e in trace.events if e.step_id in error_ids and not has_failed_ancestor(e)]
    # Earliest originating failure is the root cause.
    return min(originating, key=lambda e: e.start_time)
