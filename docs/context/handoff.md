# Handoff

## Where we are

**Phase 0 (context-readiness) complete.** The repo is scaffolded for a fresh
Claude Code session to pick up and build:

- Directory structure under `src/agent_lens/` (schema, tracing, eval, analysis,
  dashboards, ci, exporters) + `tests/`, `examples/`, `docs/`.
- **Concrete, tested `TraceEvent` contract** in `src/agent_lens/schema/`
  (`trace.py`, `eval_result.py`). This is the only non-stub code — it's the
  cross-repo contract.
- All other modules are stubs with real signatures + docstrings (`...` bodies).
- Full docs: `CLAUDE.md`, `README.md`, `docs/architecture.md`,
  `docs/contracts/*`, `docs/adr/0001-stack-and-scope.md`, `docs/orchestration.md`,
  `docs/modules/*`.
- Packaging (`pyproject.toml`, `Makefile`), ruff + pytest config.
- `examples/instrument_toy_agent.py` builds + prints a demo `Trace` today.

## Verify the scaffold

```bash
make install
make test          # schema contract tests pass
make lint
python examples/instrument_toy_agent.py
```

## Next steps (in order)

1. **Finalize the `TraceEvent` schema** in `docs/contracts/trace_event.md` —
   it's the cross-repo contract with `claims-auditor`. Confirm the field set
   against what the flagship will actually emit, then freeze `SCHEMA_VERSION`.
   *This blocks everything else.*
2. **Build `tracing` + `eval` in parallel worktrees** (see
   `docs/orchestration.md`). These two unblock the end-to-end demo and CI.
3. Then fan out `analysis`, `dashboards`, `exporters`; land `ci` (eval-gate)
   last, once a real `eval` exists to gate against.
4. Wire the GitHub Action for the eval-gate and a Grafana dashboard JSON.

## Don't forget

- `schema/` is owned centrally — change it via an ADR + dedicated PR, never
  inside a feature worktree.
- Keep `docs/modules/*.md` in sync as each module gets implemented.
- Coordinate the schema with the `claims-auditor` repo (it's the producer).
