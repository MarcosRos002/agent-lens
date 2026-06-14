"""Causal failure analysis over multi-step agent sessions.

Given a failing Trace (and optionally a cohort of traces), identify the *step*
most responsible for the failure — distinguishing the root cause from its
downstream symptoms by walking the parent_step_id tree.
"""

from agent_lens.analysis.causal import find_root_cause

__all__ = ["find_root_cause"]
