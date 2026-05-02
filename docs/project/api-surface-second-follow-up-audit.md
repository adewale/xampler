# API Surface Second Follow-up Audit

Last reviewed: 2026-05-02.

This audit follows the cleanup that canonicalized `OperationState`, made Workflows consume shared status/response helpers, documented naming policy, and added a small strict-pyright example profile.

## Executive summary

| Area | Status | Remaining concern |
|---|---|---|
| `OperationState` | Canonicalized in `xampler.status`. | No backwards-compatibility re-export from `xampler.types`; this is intentional because the shared package is still young. |
| Shared helper adoption | Workflows imports `xampler.status.OperationState` and `xampler.response.jsonable`; Gutenberg imports `xampler.streaming`. | Adoption is still narrow: only two examples consume shared modules. |
| Naming policy | Added to `docs/api/unified-api-surface.md`. | Existing examples are not mass-renamed; new examples should follow the policy. |
| Example type checking | Added `pyright.examples.json` for Workflows and R2 Data Catalog, with local stubs for `workers` and `js`. | The stubs are intentionally minimal and should not pretend to be complete Workers SDK types. |
| Backwards compatibility | No major backwards-compatibility shims remain. | The repo still uses Git dependencies on `xampler@main` inside examples, which is reproducible for users but awkward for local shared-package development. |

## Are we doing strange things for backwards compatibility?

Mostly no. The one strange-looking compatibility pattern was removed.

### Removed: self-alias re-export

We briefly had this shape:

```python
from .status import OperationState as OperationState
```

That pattern is sometimes used to mark an imported name as intentionally re-exported, but it is confusing. It has been removed. `OperationState` now lives in exactly one public place:

```python
from xampler.status import OperationState
```

`xampler.types.OperationState` is not preserved as a compatibility alias. That is acceptable because Xampler's shared helper API is not stable/public enough to justify compatibility shims that make the code harder to read.

### Still intentional but slightly unusual: examples depend on `xampler@main`

Some examples consume the shared package as users would:

```toml
"xampler @ git+https://github.com/adewale/xampler@main"
```

This is not a backwards-compatibility hack. It is a reproducibility choice: a copied example can install the shared helpers from GitHub. The trade-off is local-dev friction: when editing `xampler/` and an example together, the example may install the last pushed commit rather than the working tree.

Recommendation: keep this for user-facing examples, but document a maintainer override later, such as a local path dependency workflow or verifier option.

### Still intentional: minimal `typings/` stubs

`typings/workers.pyi` and `typings/js.pyi` exist so pyright can check selected examples without depending on complete runtime typing for Python Workers. These stubs are intentionally small. They should not grow into fake product definitions; if official stubs improve, prefer those.

## Evidence

Shared helper imports in examples now include:

| Example | Shared imports |
|---|---|
| `examples/streaming/gutenberg-stream-composition` | `xampler.streaming` |
| `examples/state-events/workflows-pipeline` | `xampler.status`, `xampler.response` |

No local examples currently duplicate `ByteStream`, `RecordStream`, `JsonlReader`, `StreamCheckpoint`, `AgentEvent`, `aiter_batches`, or `async_enumerate`.

Strict type checks now run in two layers:

```bash
uv run pyright
uv run pyright -p pyright.examples.json
```

The first checks the shared `xampler/` package. The second checks a small allowlist:

- `examples/state-events/workflows-pipeline/src`
- `examples/storage-data/r2-data-catalog/src`

## Remaining oddities and risks

| Item | Is it strange? | Why it exists | Recommendation |
|---|---|---|---|
| `xampler@main` from examples in same repo | Somewhat | User-copyable examples can install shared helpers from GitHub. | Keep for now; add maintainer local-path workflow. |
| Local `typings/` stubs | Somewhat | Official/runtime types are incomplete for strict example pyright. | Keep tiny; delete when official types are sufficient. |
| Product wrappers still local | No | Examples are tutorials; local wrappers keep each example readable. | Extract only after repeated use and strict typing. |
| Demo/Fake transports | No | Local Cloudflare parity is limited for account-backed products. | Make one demo implement `DemoTransport`; add remote profiles. |
| `.raw` in many wrappers | No | Cloudflare APIs move faster than wrappers. | Keep explicit; avoid using `.raw` in business logic. |

## Updated next cleanup order

1. Make one demo implementation explicitly conform to `xampler.types.DemoTransport`.
2. Use `xampler.streaming.ByteStream` in R2 object storage or HVSC shard ingestion.
3. Add a maintainer note for local path installs of `xampler` while editing examples.
4. Expand `pyright.examples.json` only one stable example at a time.
5. Add env-gated remote verifiers for account-backed products.

## Verdict

The cleanup direction is healthy. We are not carrying meaningful backwards-compatibility baggage. The main unusual choices are pragmatic development choices: GitHub `xampler@main` dependencies for user reproducibility and minimal local stubs for strict example type checking. Both should be documented and kept small.
