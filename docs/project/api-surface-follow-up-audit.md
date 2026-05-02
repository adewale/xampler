# API Surface Follow-up Audit

Last reviewed: 2026-05-02.

This follow-up audits the repository after the first cleanup pass (`xampler.status`, `xampler.response`, shared Gutenberg streaming imports, and `CatalogNamespace`).

## Executive summary

| Area | Status after cleanup | Remaining issue | Priority |
|---|---|---|---|
| Shared streaming helpers | Improved: Gutenberg now imports `xampler.streaming`; no local `ByteStream`/`JsonlReader` duplicates remain in examples. | Adoption is still narrow: only one example imports shared streaming helpers. R2/HVSC/AI/WebSocket examples still use their own stream/event shapes. | High |
| Shared status/response helpers | Improved: `xampler.status` and `xampler.response` exist and pass strict pyright. | Workflows now consumes them; broader adoption is still low. | Medium |
| Local wrappers | Mostly unchanged by design. | Product wrappers remain local in nearly every example. That is good for teaching, but repeated patterns still drift. | Medium |
| Naming uniformity | Improved: R2 Data Catalog now uses `CatalogNamespace`. | Product clients are still mixed: `BrowserRendering`, `AIGateway`, `R2DataCatalog`, `R2SqlClient`, `AIService`. Need an explicit naming policy. | Medium |
| Demo transports | Honest and documented. | No examples implement the shared `DemoTransport` Protocol yet; remote verifier profiles are still missing. | High |
| Type checking | Strong for `xampler/`. | Examples themselves are still mostly outside strict pyright coverage. | Medium |
| Packaging/imports | Gutenberg can consume `xampler.streaming`. | Example depends on `xampler @ git+https://github.com/adewale/xampler@main`, which can lag local changes until pushed. | Medium |

## Evidence collected

- `xampler.streaming` imports in examples: **1** (`examples/streaming/gutenberg-stream-composition`).
- Local streaming-helper duplicates in examples: **0** for `ByteStream`, `RecordStream`, `JsonlReader`, `StreamCheckpoint`, `AgentEvent`, `aiter_batches`, `async_enumerate`.
- `xampler.status` / `xampler.response` imports in examples: **1** (`examples/state-events/workflows-pipeline`).
- `.raw` escape-hatch occurrences across examples/shared package: about **80**, which is expected but should remain intentional.
- Deterministic/demo mentions across code/docs remain high because many account-backed products still need local seams.

## What got better

### 1. Streaming duplication is fixed in the Gutenberg example

`examples/streaming/gutenberg-stream-composition/src/entry.py` now imports:

```python
from xampler.streaming import (
    AgentEvent,
    ByteStream,
    JsonlReader,
    StreamCheckpoint,
    aiter_batches,
    async_enumerate,
)
```

This is the first real example-to-shared-package adoption. It validates that the shared package can be bundled into a Python Worker example.

### 2. Product-specific naming improved

R2 Data Catalog now uses `CatalogNamespace` instead of a generic `Namespace`, reducing ambiguity with KV namespaces, Durable Object namespaces, and other Cloudflare namespace concepts.

### 3. Shared low-level helper modules exist

`xampler.status` and `xampler.response` are now available and strict-type-checked. This gives future examples a place to converge on progress/checkpoint/batch and JSON/error response vocabulary.

## Remaining problems

### 1. Shared helpers exist but are not broadly consumed

Current state:

| Shared module | Exists | Used by examples | Problem |
|---|---:|---:|---|
| `xampler.streaming` | Yes | Yes, one example | Needs adoption in R2/HVSC/AI/WebSockets. |
| `xampler.status` | Yes | No | Duplicated concepts remain in Workflows, Queues, HVSC, Gutenberg, Agents. |
| `xampler.response` | Yes | No | Many examples still manually shape JSON/error responses. |
| `xampler.types` | Yes | No | `NewType`, `SupportsRaw`, `DemoTransport`, `RemoteVerifier` are not driving examples yet. |

Recommendation: the next cleanup should not create more shared modules. It should consume the existing ones in 2-3 representative examples.

### 2. `OperationState` is canonicalized

`OperationState` now lives only in `xampler.status`. `xampler.types` no longer re-exports it just for compatibility because the package is not stable enough to justify confusing aliases.

### 3. Product wrapper naming still has two competing styles

There are two legitimate naming styles in the repo:

| Style | Examples | When it is good |
|---|---|---|
| Product noun | `BrowserRendering`, `AIGateway`, `R2DataCatalog` | Clear product facade; concise in docs. |
| Role suffix | `R2SqlClient`, `QueueService`, `WorkflowService`, `VectorIndex` | Clear whether the object is a REST client, binding service, or resource. |

Recommendation: document this as policy instead of renaming everything:

- Use `*Service` for native Worker bindings that perform actions.
- Use `*Client` for REST/API-token clients.
- Use product nouns only when the official product name is itself the clearest facade.
- Use `*Ref` for passive handles and `*Session` for active conversational/stateful interactions.
- Use `Demo*` only for deterministic product stand-ins; use `Fake*` only for raw test harness objects.

### 4. Demo seams are not protocol-shaped yet

Examples use `DemoAIService`, `DemoVectorIndex`, `DemoWorkflowService`, `DemoR2SqlClient`, `DemoR2DataCatalog`, `DemoPostgres`, and `DemoAgent`, but none implement/import `xampler.types.DemoTransport`.

Recommendation: choose one example with a clean request/result pair, probably Workers AI or R2 SQL, and make its demo implementation conform to `DemoTransport[Request, Result]`. Then repeat only where it improves readability.

### 5. Strict type checking stops at `xampler/`

This is intentional for now, but it means wrapper drift in examples will not be caught by pyright.

Recommendation: add a second pyright profile for a small allowlist of stable examples:

1. `examples/streaming/gutenberg-stream-composition/src`
2. `examples/storage-data/r2-object-storage/src`
3. `examples/storage-data/d1-database/src`
4. `examples/state-events/queues-producer-consumer/src`

Do not enable strict checking for every example at once.

### 6. Example package dependency on `xampler@main` is useful but has local-dev friction

The Gutenberg example now depends on:

```toml
"xampler @ git+https://github.com/adewale/xampler@main"
```

This proves examples can consume the shared package as users would, but local changes to `xampler/` are not visible to that example until pushed.

Recommendation: keep the Git dependency for user-facing reproducibility, but add a maintainer note or verifier override for local path installs when changing shared package APIs.

## Next cleanup pass

Recommended order:

1. Convert Workers AI or R2 SQL demo class to explicitly satisfy `DemoTransport`.
2. Use `xampler.streaming.ByteStream` in the R2 object wrapper or HVSC shard reader.
3. Expand the pyright example allowlist only after the current two examples stay stable.
4. Add env-gated remote verifier profiles for account-backed products.

## Verdict

The cleanup moved the repo in the right direction: shared streaming is now real, naming is slightly cleaner, and shared status/response modules exist. The main issue has shifted from **missing shared helpers** to **low adoption of shared helpers**. The next improvements should be consumption-focused rather than abstraction-focused.
