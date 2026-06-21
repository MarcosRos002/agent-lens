"""Trace capture primitives — instrument an agent into a canonical ``Trace``.

Developer-facing ergonomics: ``trace_session()`` opens a root (one ``session_id``)
and ``trace_step()`` opens a child step that becomes one ``TraceEvent`` on exit,
with ``parent_step_id`` linkage derived from the nesting. The active session/parent
live in ``contextvars`` so nesting works across function calls without threading
state by hand. ``TraceEvent`` is OTel-friendly, so a span exporter can be layered
on later without changing this API.

    with trace_session() as session:
        with trace_step(kind="tool", tool_name="search") as step:
            step.record_output(result)
    trace = session.trace
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

from agent_lens.schema import ErrorInfo, StepKind, StepStatus, TokenUsage, Trace, TraceEvent

_current_session: ContextVar[Session | None] = ContextVar("agent_lens_session", default=None)


def _as_kind(kind: StepKind | str) -> StepKind:
    if isinstance(kind, StepKind):
        return kind
    try:
        return StepKind(kind)
    except ValueError:
        return StepKind.OTHER


class Step:
    """Mutable handle for the in-flight step; finalized into a TraceEvent on exit."""

    def __init__(self) -> None:
        self.inputs: dict[str, Any] = {}
        self.output: Any | None = None
        self.model: str | None = None
        self.provider: str | None = None
        self.tokens = TokenUsage()
        self.cost_usd: float | None = None
        self.metadata: dict[str, Any] = {}

    def record_input(self, **inputs: Any) -> None:
        self.inputs.update(inputs)

    def record_output(self, output: Any) -> None:
        self.output = output

    def record_model(
        self,
        model: str,
        *,
        provider: str | None = None,
        total_tokens: int = 0,
        cost_usd: float | None = None,
    ) -> None:
        self.model = model
        self.provider = provider
        self.tokens = TokenUsage(total_tokens=total_tokens)
        self.cost_usd = cost_usd

    def add_metadata(self, **kv: Any) -> None:
        self.metadata.update(kv)


class Session:
    """Collects the steps of one run; exposes the assembled ``Trace``."""

    def __init__(self, session_id: str, metadata: dict[str, Any]) -> None:
        self.session_id = session_id
        self.metadata = metadata
        self.events: list[TraceEvent] = []
        self._parents: list[str] = []  # stack of enclosing step_ids

    @property
    def current_parent(self) -> str | None:
        return self._parents[-1] if self._parents else None

    @property
    def trace(self) -> Trace:
        return Trace(session_id=self.session_id, events=list(self.events), metadata=self.metadata)


@contextmanager
def trace_session(
    *, session_id: str | None = None, metadata: dict[str, Any] | None = None
) -> Iterator[Session]:
    """Open a root context that groups all steps into one session/trace."""
    session = Session(session_id or uuid.uuid4().hex, metadata or {})
    token = _current_session.set(session)
    try:
        yield session
    finally:
        _current_session.reset(token)


@contextmanager
def trace_step(
    *,
    name: str | None = None,
    kind: StepKind | str = StepKind.OTHER,
    tool_name: str | None = None,
) -> Iterator[Step]:
    """Open a child step that becomes one TraceEvent on exit."""
    session = _current_session.get()
    if session is None:
        raise RuntimeError("trace_step() must be used inside a trace_session()")

    resolved_kind = _as_kind(kind)
    step_id = uuid.uuid4().hex
    parent = session.current_parent
    handle = Step()
    session._parents.append(step_id)

    start_time = datetime.now(UTC)
    t0 = perf_counter()
    status, error = StepStatus.OK, None
    try:
        yield handle
    except Exception as exc:
        status = StepStatus.ERROR
        error = ErrorInfo(type=type(exc).__name__, message=str(exc))
        raise
    finally:
        session._parents.pop()
        session.events.append(
            TraceEvent(
                session_id=session.session_id,
                step_id=step_id,
                parent_step_id=parent,
                kind=resolved_kind,
                name=name or tool_name or resolved_kind.value,
                tool_name=tool_name,
                inputs=handle.inputs,
                output=handle.output,
                model=handle.model,
                provider=handle.provider,
                tokens=handle.tokens,
                cost_usd=handle.cost_usd,
                latency_ms=(perf_counter() - t0) * 1000.0,
                start_time=start_time,
                end_time=datetime.now(UTC),
                status=status,
                error=error,
                metadata=handle.metadata,
            )
        )
