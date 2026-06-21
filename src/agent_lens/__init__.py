"""agent-lens — eval + observability for LLM agents.

Best entry points:
- The canonical contract lives in ``agent_lens.schema`` (TraceEvent, EvalResult).
- See CLAUDE.md and docs/ for architecture, contracts, and orchestration.

Most submodules are Phase-0 stubs; the ``schema`` package is concrete because
it is the cross-repo contract other repos depend on.
"""

from agent_lens.analysis.causal import find_root_cause
from agent_lens.dashboards.prometheus import PrometheusExporter
from agent_lens.eval.heuristic import ToolCallCorrectnessEvaluator
from agent_lens.eval.llm_judge import TrajectoryJudgeEvaluator
from agent_lens.exporters.langfuse import LangfuseExporter
from agent_lens.exporters.langsmith import LangSmithExporter
from agent_lens.metrics import TraceMetrics, compute_trace_metrics, metrics_as_schema
from agent_lens.schema import (
    EvalReport,
    EvalResult,
    Metric,
    Trace,
    TraceEvent,
)
from agent_lens.tracing.capture import trace_session, trace_step

__version__ = "0.0.1"

__all__ = [
    "EvalReport",
    "EvalResult",
    "Metric",
    "Trace",
    "TraceEvent",
    "TraceMetrics",
    "compute_trace_metrics",
    "metrics_as_schema",
    "ToolCallCorrectnessEvaluator",
    "TrajectoryJudgeEvaluator",
    "find_root_cause",
    "PrometheusExporter",
    "LangfuseExporter",
    "LangSmithExporter",
    "trace_session",
    "trace_step",
    "__version__",
]
