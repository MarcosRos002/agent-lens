"""Trace capture primitives backed by OpenTelemetry spans.

Phase 0 stub: signatures and docstrings only. The concrete implementation maps
each span to a ``TraceEvent`` and assigns session_id/step_id/parent_step_id from
the active OTel context.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from agent_lens.schema import StepKind


@contextmanager
def trace_session(
    *, session_id: str | None = None, metadata: dict[str, Any] | None = None
) -> Iterator[Any]:  # pragma: no cover - Phase 0 stub
    """Open a root context that groups all steps into one session/trace."""
    ...
    yield None


@contextmanager
def trace_step(
    *,
    name: str | None = None,
    kind: StepKind | str = StepKind.OTHER,
    tool_name: str | None = None,
) -> Iterator[Any]:  # pragma: no cover - Phase 0 stub
    """Open a child step (OTel span) that becomes one TraceEvent on exit."""
    ...
    yield None
