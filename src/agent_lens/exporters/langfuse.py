"""Langfuse-compatible exporter (Phase 0 stub)."""

from __future__ import annotations

from agent_lens.schema import Trace


class LangfuseExporter:
    """Maps a canonical Trace onto Langfuse traces/observations (Phase 0 stub)."""

    def __init__(self, *, public_key: str | None = None, secret_key: str | None = None) -> None:
        self.public_key = public_key
        self.secret_key = secret_key

    def export(self, trace: Trace) -> None:  # pragma: no cover - Phase 0 stub
        ...
