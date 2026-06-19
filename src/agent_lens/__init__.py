"""agent-lens — eval + observability for LLM agents.

Best entry points:
- The canonical contract lives in ``agent_lens.schema`` (TraceEvent, EvalResult).
- See CLAUDE.md and docs/ for architecture, contracts, and orchestration.

Most submodules are Phase-0 stubs; the ``schema`` package is concrete because
it is the cross-repo contract other repos depend on.
"""

from agent_lens.eval.heuristic import ToolCallCorrectnessEvaluator
from agent_lens.metrics import TraceMetrics, compute_trace_metrics, metrics_as_schema
from agent_lens.schema import (
    EvalReport,
    EvalResult,
    Metric,
    Trace,
    TraceEvent,
)

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
    "__version__",
]
