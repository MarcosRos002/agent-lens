"""LangSmith-compatible exporter (Phase 0 stub)."""

from __future__ import annotations

from agent_lens.schema import Trace


class LangSmithExporter:
    """Maps a canonical Trace onto LangSmith runs (Phase 0 stub)."""

    def __init__(self, *, api_key: str | None = None, project: str | None = None) -> None:
        self.api_key = api_key
        self.project = project

    def export(self, trace: Trace) -> None:  # pragma: no cover - Phase 0 stub
        ...
