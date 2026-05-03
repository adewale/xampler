# Competitive positioning

## Python ecosystem

Xampler is strongest as a Pythonic Cloudflare learning library with executable examples. It is not yet as mature as the best Python developer-experience projects.

| Competitor | Where they are ahead | Why Xampler has not caught up yet |
|---|---|---|
| FastAPI | First-run simplicity, type-driven routing, automatic docs, one memorable mental model. | Xampler spans many Cloudflare products, remote credentials, Worker bindings, Pyodide constraints, and paid/account-backed services. The problem space is broader and less uniform than HTTP routing. |
| LangChain / LlamaIndex | Compositional vocabulary, chain/agent storytelling, many copyable patterns. | Xampler optimizes for runtime honesty and Cloudflare primitives, so it cannot hide setup/cost/topology behind a single abstraction without lying. |
| Prefect / Dagster | Operational model, retries/state/checkpoints, observability UI, pipeline lifecycle. | Xampler has `Progress`, `Checkpoint`, Queue results, and Workflow status, but it does not yet have a unified orchestration layer or UI. |
| boto3 / Google / Azure SDKs | Stable releases, credential providers, generated references, broad API coverage. | Xampler is pre-0.1 and intentionally pruning young APIs before promising compatibility. |

## WebAssembly and Workers language projects

Rust and Zig Workers projects are instructive because they treat WebAssembly as a first-class constraint rather than an implementation detail.

| Project family | What they do well | What Xampler should learn |
|---|---|---|
| Cloudflare Rust Workers / `workers-rs` | Compile-time safety, explicit Workers bindings, good WASM mental model, performance expectations. | Keep Pyodide/WASM constraints visible, preserve Cloudflare vocabulary, and use strict typing/tests to compensate for Python's looser runtime. |
| Zig Workers experiments | Tiny runtime boundary, explicit host calls, low-level control, startup/performance discipline. | Keep `cfboundary` small, avoid hiding JS/Python conversion, keep examples focused, and document when data crosses into Python memory. |
| TypeScript Workers | First-class platform support, official docs, fastest path to every new Workers API. | Position Xampler as a Pythonic layer for Python users, not as a replacement for native Workers APIs. Keep `.raw` escape hatches. |

## Current Xampler advantages

- Importable product wrappers plus executable examples.
- Fakeable bindings and `Demo*` transports.
- Explicit local/remote/prepare/cleanup lifecycle.
- `xc` makes the workflow memorable.
- Strong runtime honesty around paid products and Pyodide constraints.

## What to improve next

1. Deepen per-module API references beyond snippets.
2. Run credentialed remote profiles and record pass/fail.
3. Add `docs/api/composition-and-operations.md` examples to Workflows, Queues, Gutenberg, and HVSC routes.
4. Keep pre-0.1 APIs sharp: one CLI name, one canonical import path, no compatibility shims.
