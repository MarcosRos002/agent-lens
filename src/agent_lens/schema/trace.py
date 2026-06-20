"""Canonical TraceEvent schema — THE cross-repo contract.

This module defines the wire format that any instrumented agent (notably the
flagship ``claims-auditor``) emits and that ``agent-lens`` consumes for eval,
analysis, and dashboards.

DESIGN NOTES (why this is concrete and not a stub):
- This schema is a *contract*. Other repos serialize against it. Changing a
  field is a breaking change and must go through docs/contracts/trace_event.md
  + an ADR. Treat it like a public API.
- A ``TraceEvent`` is ONE STEP in a session. A full agent run is an ordered
  list of TraceEvents sharing a ``session_id``, linked into a tree via
  ``parent_step_id``. Trace-level (not call-level) evaluation is the whole point
  of agent-lens, so the parent/child linkage is first-class.
- Field names and semantics are intentionally OTel-friendly so a TraceEvent
  maps cleanly onto an OpenTelemetry span (see src/agent_lens/tracing).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

SCHEMA_VERSION = "0.1.0"


class StepKind(str, Enum):
    """What a single step in an agent trace represents."""

    LLM = "llm"  # a model call (reasoning / generation)
    TOOL = "tool"  # a tool / function invocation
    RETRIEVAL = "retrieval"  # a RAG / vector-store lookup
    AGENT = "agent"  # a sub-agent / nested agent invocation
    GUARDRAIL = "guardrail"  # a validation / safety / policy check
    OTHER = "other"


class StepStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TokenUsage(BaseModel):
    """Token accounting for an LLM step. Zeros for non-LLM steps."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    # Cache-aware fields (Anthropic/OpenRouter prompt caching) — optional.
    cache_read_tokens: int | None = None
    cache_write_tokens: int | None = None


class ErrorInfo(BaseModel):
    """Structured error payload when ``status != ok``."""

    type: str = Field(..., description="Exception/class name or error code.")
    message: str = Field(..., description="Human-readable error message.")
    retryable: bool | None = Field(
        None, description="Whether the agent could have retried this step."
    )
    stack: str | None = Field(None, description="Optional stack trace (truncate before emit).")


class TraceEvent(BaseModel):
    """One step in an agent session. The atomic unit agent-lens consumes.

    Identity / linkage
    ------------------
    - ``session_id``: groups all steps of one agent run (a "trace").
    - ``step_id``: unique id of THIS step within the session.
    - ``parent_step_id``: the step that caused this one (``None`` for the root).
      This forms the trajectory tree used by trajectory/causal evaluators.
    """

    # --- schema metadata ---
    schema_version: str = Field(default=SCHEMA_VERSION, description="Schema version for compat.")

    # --- identity & linkage ---
    session_id: str = Field(..., description="Groups all steps of one agent run.")
    step_id: str = Field(..., description="Unique id of this step within the session.")
    parent_step_id: str | None = Field(
        None, description="Id of the causing step; None for the root step."
    )

    # --- what happened ---
    kind: StepKind = Field(..., description="Category of step (llm/tool/retrieval/...).")
    name: str = Field(
        ...,
        description="Human-readable step name (e.g. tool name, agent node, or model role).",
    )
    tool_name: str | None = Field(
        None, description="Tool/function name when kind == TOOL (None otherwise)."
    )

    # --- payload ---
    inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Step inputs (args, prompt, query). Redact PII before emit.",
    )
    output: Any | None = Field(
        None, description="Step output (tool return, model completion, retrieved docs)."
    )

    # --- model / cost / perf ---
    model: str | None = Field(
        None, description="Model identifier for LLM steps, e.g. 'claude-sonnet-4'."
    )
    provider: str | None = Field(
        None, description="Provider id, e.g. 'anthropic' | 'openrouter' | 'openai'."
    )
    tokens: TokenUsage = Field(default_factory=TokenUsage)
    cost_usd: float | None = Field(
        None, description="Computed USD cost for this step (provider price * tokens)."
    )
    latency_ms: float | None = Field(None, description="Wall-clock duration of this step in ms.")

    # --- timing ---
    start_time: datetime = Field(..., description="Step start (UTC, timezone-aware).")
    end_time: datetime | None = Field(None, description="Step end (UTC). None while in-flight.")

    # --- outcome ---
    status: StepStatus = Field(default=StepStatus.OK)
    error: ErrorInfo | None = Field(None, description="Set when status indicates failure.")

    # --- free-form context ---
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary tags: env, git sha, model_version, prompt_version, user/ab bucket.",
    )

    @model_validator(mode="after")
    def _check_error_consistency(self) -> TraceEvent:
        if self.status == StepStatus.ERROR and self.error is None:
            raise ValueError("status=='error' requires an 'error' payload")
        return self


class Trace(BaseModel):
    """A whole agent run: an ordered list of TraceEvents sharing a session_id.

    This is the unit that trace-level evaluators and causal analysis operate on.
    """

    session_id: str
    events: list[TraceEvent] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_session_ids(self) -> Trace:
        for ev in self.events:
            if ev.session_id != self.session_id:
                raise ValueError(
                    f"event {ev.step_id} has session_id={ev.session_id!r}, "
                    f"expected {self.session_id!r}"
                )
        return self
