"""Tests for the Langfuse/LangSmith exporters (canonical Trace -> platform schema)."""

from __future__ import annotations

from datetime import UTC, datetime

from agent_lens.exporters.langfuse import LangfuseExporter
from agent_lens.exporters.langsmith import LangSmithExporter
from agent_lens.schema import (
    ErrorInfo,
    StepKind,
    StepStatus,
    TokenUsage,
    Trace,
    TraceEvent,
)


def _trace() -> Trace:
    root = TraceEvent(
        session_id="s1",
        step_id="root",
        kind=StepKind.AGENT,
        name="audit",
        start_time=datetime(2026, 1, 1, tzinfo=UTC),
    )
    llm = TraceEvent(
        session_id="s1",
        step_id="llm1",
        parent_step_id="root",
        kind=StepKind.LLM,
        name="classify",
        model="sonnet",
        cost_usd=0.003,
        tokens=TokenUsage(total_tokens=120),
        start_time=datetime(2026, 1, 1, tzinfo=UTC),
    )
    err = TraceEvent(
        session_id="s1",
        step_id="rag1",
        parent_step_id="root",
        kind=StepKind.RETRIEVAL,
        name="retrieve",
        status=StepStatus.ERROR,
        error=ErrorInfo(type="Timeout", message="db down"),
        start_time=datetime(2026, 1, 1, tzinfo=UTC),
    )
    return Trace(session_id="s1", events=[root, llm, err])


# --------------------------------------------------------------------------- #
# Langfuse
# --------------------------------------------------------------------------- #
def test_langfuse_maps_each_event_to_an_observation() -> None:
    obs = LangfuseExporter().to_observations(_trace())
    assert len(obs) == 3
    assert {o["id"] for o in obs} == {"root", "llm1", "rag1"}
    assert all(o["traceId"] == "s1" for o in obs)


def test_langfuse_llm_is_generation_others_are_spans() -> None:
    by_id = {o["id"]: o for o in LangfuseExporter().to_observations(_trace())}
    assert by_id["llm1"]["type"] == "GENERATION"
    assert by_id["root"]["type"] == "SPAN"
    assert by_id["llm1"]["model"] == "sonnet"
    assert by_id["llm1"]["usage"]["totalTokens"] == 120


def test_langfuse_preserves_parent_linkage_and_error_level() -> None:
    by_id = {o["id"]: o for o in LangfuseExporter().to_observations(_trace())}
    assert by_id["llm1"]["parentObservationId"] == "root"
    assert by_id["rag1"]["level"] == "ERROR"
    assert "db down" in by_id["rag1"]["statusMessage"]


# --------------------------------------------------------------------------- #
# LangSmith
# --------------------------------------------------------------------------- #
def test_langsmith_maps_run_types() -> None:
    by_id = {r["id"]: r for r in LangSmithExporter().to_runs(_trace())}
    assert by_id["llm1"]["run_type"] == "llm"
    assert by_id["rag1"]["run_type"] == "retriever"
    assert by_id["root"]["run_type"] == "chain"


def test_langsmith_preserves_linkage_error_and_usage() -> None:
    by_id = {r["id"]: r for r in LangSmithExporter().to_runs(_trace())}
    assert by_id["llm1"]["parent_run_id"] == "root"
    assert by_id["llm1"]["extra"]["tokens"] == 120
    assert by_id["llm1"]["extra"]["cost_usd"] == 0.003
    assert by_id["rag1"]["error"] and "db down" in by_id["rag1"]["error"]
