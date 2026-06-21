"""LangSmith-compatible exporter.

Maps the canonical ``Trace`` onto LangSmith runs. The mapping (``to_runs``) is
pure and tested; ``export`` lazily pushes via the SDK.
"""

from __future__ import annotations

from typing import Any

from agent_lens.schema import StepKind, Trace, TraceEvent

# Canonical step kind -> LangSmith run_type.
_RUN_TYPE: dict[StepKind, str] = {
    StepKind.LLM: "llm",
    StepKind.TOOL: "tool",
    StepKind.RETRIEVAL: "retriever",
    StepKind.AGENT: "chain",
    StepKind.GUARDRAIL: "tool",
    StepKind.OTHER: "chain",
}


def _run(e: TraceEvent) -> dict[str, Any]:
    return {
        "id": e.step_id,
        "trace_id": e.session_id,
        "parent_run_id": e.parent_step_id,
        "name": e.name,
        "run_type": _RUN_TYPE.get(e.kind, "chain"),
        "inputs": e.inputs,
        "outputs": {"output": e.output} if e.output is not None else {},
        "start_time": e.start_time.isoformat(),
        "end_time": e.end_time.isoformat() if e.end_time else None,
        "error": e.error.message if e.error else None,
        "extra": {"model": e.model, "tokens": e.tokens.total_tokens, "cost_usd": e.cost_usd},
    }


class LangSmithExporter:
    """Maps a canonical Trace onto LangSmith runs."""

    def __init__(self, *, api_key: str | None = None, project: str | None = None) -> None:
        self.api_key = api_key
        self.project = project

    def to_runs(self, trace: Trace) -> list[dict[str, Any]]:
        """Map each TraceEvent to a LangSmith run dict (pure)."""
        return [_run(e) for e in trace.events]

    def export(self, trace: Trace) -> None:  # pragma: no cover - network/SDK
        """Push the trace to LangSmith via the SDK (lazily imported)."""
        from langsmith import Client

        client = Client(api_key=self.api_key)
        for run in self.to_runs(trace):
            client.create_run(project_name=self.project, **run)
