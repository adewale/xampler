# API Surface Third Follow-up Audit

Last reviewed: 2026-05-02.

This audit checks the state after `48fdd8b Canonicalize status helpers and audit API surface`.

## Verification status

Passed:

```bash
uv run ruff check .
uv run pyright
uv run pyright -p pyright.examples.json
uv run pytest -q
```

Markdown link check: **0 broken local links**.

## Summary

| Area | Current state | Assessment |
|---|---|---|
| Canonical status type | `OperationState` exists only in `xampler.status`. | Good. No strange compatibility alias remains. |
| Shared helper adoption | Gutenberg uses `xampler.streaming`; Workflows uses `xampler.status` and `xampler.response`. | Better, but still only 2 examples consume shared helpers. |
| Example strict typing | `pyright.examples.json` checks Workflows and R2 Data Catalog. | Good start; keep allowlist small. |
| Runtime stubs | `typings/workers.pyi` and `typings/js.pyi` support selected example pyright. | Acceptable if kept minimal. |
| Demo transport Protocol | `DemoTransport` exists in `xampler.types`. | Not used by examples yet. |
| Local product wrappers | Most wrappers remain example-local. | Intentional for tutorial readability. |
| `xampler@main` dependencies | Gutenberg and Workflows depend on `xampler @ git+...@main`. | Useful for user reproducibility; awkward for local development. |

## Are we doing strange things for backwards compatibility?

No meaningful backwards-compatibility hacks are currently in code.

### Removed compatibility-ish alias

The earlier self-alias form is gone from code:

```python
from .status import OperationState as OperationState
```

There is also no `xampler.types.OperationState` compatibility alias. This is the right choice for now: the shared helper package is still pre-stable, so preserving every transient import path would create confusing API baggage.

### Historical docs mention the old alias

Some audit docs still mention the removed self-alias in a historical section. That is not a compatibility mechanism; it is an audit record explaining what was removed.

### Current unusual-but-intentional choices

| Choice | Strange? | Why acceptable | Watch item |
|---|---|---|---|
| Example-local product wrappers | No | Examples should be readable standalone tutorials. | Extract only stable patterns with repeated use. |
| Minimal `typings/` stubs | Slightly | Needed for strict pyright on selected examples without pretending to type the full Workers runtime. | Keep tiny; prefer official stubs if they improve. |
| Examples depend on `xampler@main` | Slightly | Lets copied examples install shared helpers from GitHub. | Add maintainer local-path workflow for shared-package edits. |
| Audit docs accumulate | Slightly | Useful project history. | Consider a single current-state audit plus archived older audits later. |

## Evidence

Shared helper imports in examples:

| Example | Shared module used |
|---|---|
| `examples/streaming/gutenberg-stream-composition` | `xampler.streaming` |
| `examples/state-events/workflows-pipeline` | `xampler.status`, `xampler.response` |

Local duplicate streaming helper definitions in examples:

- `ByteStream`: none
- `RecordStream`: none
- `JsonlReader`: none
- `StreamCheckpoint`: none
- `AgentEvent`: none
- `aiter_batches`: none
- `async_enumerate`: none

Strict example pyright allowlist:

- `examples/state-events/workflows-pipeline/src`
- `examples/storage-data/r2-data-catalog/src`

Examples that depend on shared `xampler` from GitHub:

- `examples/streaming/gutenberg-stream-composition`
- `examples/state-events/workflows-pipeline`

## Remaining issues

### 1. Shared helpers are still under-adopted

`xampler.status`, `xampler.response`, and `xampler.types` are now real, but most examples still use local dataclass/result/response shaping.

Next best targets:

1. Queues: use `xampler.status.BatchResult` or align its `QueueBatchResult` shape.
2. Workers AI or R2 SQL: make a demo class conform to `DemoTransport`.
3. HVSC: use `xampler.streaming.ByteStream` / `JsonlReader` for catalog shards where practical.

### 2. `DemoTransport` is not exercised

The Protocol exists, but no example proves it improves readability. Avoid broad conversion. Pick one clean example first.

Best candidate: Workers AI, because it has a clear request/result pair:

```text
TextGenerationRequest -> TextGenerationResponse
```

### 3. Type checking examples will expose Worker typing limits

The `typings/` stubs let pyright check selected examples, but expanding too quickly will require either many ignores or fake runtime definitions.

Rule: add one example at a time only when its wrapper logic is stable and the required stubs stay small.

### 4. Local development with `xampler@main` is frictional

When editing `xampler/` and an example simultaneously, pywrangler installs the pushed Git version. That can hide local changes until after push.

Recommendation: add a maintainer-only note, not a default user workflow:

```text
For shared-package development, temporarily switch the example dependency to a local path or install the working tree before running pywrangler.
```

## Updated recommendation

Do not add more abstractions right now. The next useful work is adoption:

1. Convert one `Demo*` class to satisfy `DemoTransport`.
2. Convert one data-heavy example to consume `xampler.streaming` beyond Gutenberg.
3. Add a short maintainer note for local `xampler` development.
4. Add at most one more strict-pyright example after that.

## Verdict

The codebase is cleaner than the previous audit. There are no active weird backwards-compatibility shims. The main risk is now process-oriented: shared helpers can become decorative unless more examples consume them, and strict example typing can become noisy if expanded too quickly.
