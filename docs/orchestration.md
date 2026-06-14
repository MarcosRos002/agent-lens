# Orchestration — build order & parallel worktrees

How to build agent-lens with multiple Claude Code agents working in parallel
without stepping on each other. The rule is simple: **the contract is built
first and alone; everything else fans out in parallel behind it.**

## Dependency graph

```
                     ┌─────────────────────────────┐
                     │   schema/  (TraceEvent etc.) │   FOUNDATIONAL
                     │   — BLOCKS EVERYTHING —      │   build first, alone
                     └──────────────┬──────────────┘
                                    │ everyone imports this
        ┌───────────────┬──────────┼──────────┬───────────────┬───────────────┐
        ▼               ▼          ▼          ▼               ▼               ▼
   ┌─────────┐    ┌──────────┐ ┌──────────┐ ┌──────────┐  ┌──────────┐  ┌───────────┐
   │ tracing │    │   eval   │ │ analysis │ │dashboards│  │    ci    │  │ exporters │
   └─────────┘    └──────────┘ └──────────┘ └──────────┘  └──────────┘  └───────────┘
   PARALLEL — independent worktrees, each owned by a separate agent
```

Soft edges (not blocking, coordinate at integration):
- `ci` consumes `eval`'s `EvalReport` — agree on the report shape (already fixed
  by the `schema` contract), then build independently.
- `dashboards`, `analysis`, `exporters` all read `Trace`; no code dependency on
  each other.

## Phase plan

1. **Phase 0 — context readiness (DONE).** Structure, docs, concrete
   `TraceEvent` contract + tests, stubs. (This commit.)
2. **Phase 1a — finalize the contract.** Lock `TraceEvent` in
   `docs/contracts/trace_event.md` *with* the claims-auditor side. This is the
   gate: nothing parallel starts until the schema is frozen, because all six
   modules import it.
3. **Phase 1b — parallel build.** Spin up one worktree per module below.

## Parallel worktrees (one Claude Code agent each)

Once the schema is frozen, create an isolated git worktree per module so agents
never share a working tree:

```bash
# from the repo root, branch + worktree per module
git worktree add ../agent-lens-tracing   -b feat/tracing
git worktree add ../agent-lens-eval      -b feat/eval
git worktree add ../agent-lens-analysis  -b feat/analysis
git worktree add ../agent-lens-dashboards -b feat/dashboards
git worktree add ../agent-lens-ci        -b feat/ci
git worktree add ../agent-lens-exporters -b feat/exporters
```

Then open a separate Claude Code session in each worktree directory. Each agent:
- reads `CLAUDE.md`, `docs/architecture.md`, its own `docs/modules/<mod>.md`, and
  the contract docs;
- implements behind the **existing stub signatures** (do not change `schema/`);
- adds tests under `tests/`;
- opens a PR to `main`.

Integration order for merging PRs: `tracing` and `eval` first (they unblock the
demo and CI), then `analysis` / `dashboards` / `exporters`, then `ci` (it depends
on a real `eval` to gate against). Clean up worktrees with
`git worktree remove <path>` after merge.

## Coordination rules

- **`schema/` is owned centrally.** A module needing a schema change files an ADR
  and a `schema` PR first; it does not edit `schema/` inside its feature worktree.
- Keep each module's public surface matching its `docs/modules/*.md` so siblings
  can integrate without reading each other's internals.
- Every PR runs `make lint` + `make test`; once `ci` lands, the eval-gate runs too.
