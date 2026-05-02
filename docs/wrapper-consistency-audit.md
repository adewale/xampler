# Wrapper Consistency and Type-System Audit

Last reviewed: 2026-05-02.

## What is consistent

- Most primitives use a service wrapper around the Cloudflare binding.
- Many examples use dataclasses for request/result models.
- `.raw` appears in the strongest wrappers and should become mandatory.
- Deterministic demo transports now exist for account-backed primitives.
- Verification is centralized in `scripts/verify_examples.py`.

## Duplication to remove

| Duplication | Fix |
|---|---|
| Repeated `Response.json`/error helpers | Add shared `xampler.response` helpers. |
| Repeated demo transport pattern | Add `Protocol` interfaces for real/demo clients. |
| Repeated dataclass-to-JSON conversion | Add `to_jsonable()` boundary helper. |
| Repeated status/progress models | Share `Progress`, `Checkpoint`, `OperationStatus`. |
| Streaming helpers isolated in one example | Lift `ByteStream`, `JsonlReader`, `aiter_batches`, `StreamCheckpoint` into shared package. |

## Type-system opportunities

Modern Python can make the API more precise:

- `Protocol` for swappable real/demo transports.
- `TypeVar` + `Generic` for typed record streams and `one_as(Model)` results.
- `Literal` for constrained states: `"running" | "complete" | "failed"`.
- `TypedDict` for Cloudflare JSON payloads that should remain dictionaries.
- `Self` for fluent builders such as query builders and multipart uploads.
- `NewType` for IDs and keys: `R2Key`, `QueueName`, `WorkflowId`, `VectorId`.
- `Annotated` for documented constraints: dimensions, batch sizes, content types.
- `assert_never()` for exhaustive state handling.

## Type verification tooling to add

| Tool | Why |
|---|---|
| `pyright` | Strong static checking for modern typing and Pyodide-compatible code. |
| `mypy` | Optional second checker for library-like wrappers. |
| `ruff` | Already used; keep strict linting. |
| `pytest` | Already used; expand wrapper unit tests. |

## Current gap

We are using dataclasses well, but we are not yet treating wrappers as a reusable typed library. The next refactor should create a small shared `xampler` package with typed protocols, streaming primitives, response helpers, and common Cloudflare boundary conversions.
