"""Langfuse-compatible exporter.

Maps the canonical ``Trace`` onto Langfuse observations so teams already on
Langfuse can adopt agent-lens's evaluators without re-instrumenting. The mapping
(``to_observations``) is pure and tested; ``export`` lazily pushes via the SDK.
"""

from __future__ import annotations

from typing import Any

from agent_lens.schema import StepKind, StepStatus, Trace, TraceEvent


def _observation(e: TraceEvent) -> dict[str, Any]:
    return {
        "id": e.step_id,
        "traceId": e.session_id,
        "parentObservationId": e.parent_step_id,
        "type": "GENERATION" if e.kind is StepKind.LLM else "SPAN",
        "name": e.name,
        "input": e.inputs or None,
        "output": e.output,
        "model": e.model,
        "usage": {"totalTokens": e.tokens.total_tokens},
        "startTime": e.start_time.isoformat(),
        "endTime": e.end_time.isoformat() if e.end_time else None,
        "level": "ERROR" if e.status is StepStatus.ERROR else "DEFAULT",
        "statusMessage": e.error.message if e.error else None,
        "metadata": {"provider": e.provider, "cost_usd": e.cost_usd, **e.metadata},
    }


class LangfuseExporter:
    """Maps a canonical Trace onto Langfuse traces/observations."""

    def __init__(self, *, public_key: str | None = None, secret_key: str | None = None) -> None:
        self.public_key = public_key
        self.secret_key = secret_key

    def to_observations(self, trace: Trace) -> list[dict[str, Any]]:
        """Map each TraceEvent to a Langfuse observation dict (pure)."""
        return [_observation(e) for e in trace.events]

    def export(self, trace: Trace) -> None:  # pragma: no cover - network/SDK
        """Push the trace to Langfuse via the SDK (lazily imported)."""
        from langfuse import Langfuse

        client = Langfuse(public_key=self.public_key, secret_key=self.secret_key)
        for obs in self.to_observations(trace):
            client.trace(id=obs["traceId"]).span(**obs)
