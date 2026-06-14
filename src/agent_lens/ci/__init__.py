"""CI eval-gate: block merges on eval regression.

Runs an eval suite over a set of traces and compares against a stored baseline.
Fails (non-zero exit) when a gated metric regresses beyond tolerance — e.g. when
a model/prompt version bump drops trajectory score. Wired into GitHub Actions
(see .github/workflows and docs/modules/ci.md).
"""

from agent_lens.ci.gate import EvalGate, GateOutcome

__all__ = ["EvalGate", "GateOutcome"]
