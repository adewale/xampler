# Example and API improvement ideas

Goal: keep Xampler consistent and simple by reusing a few Pythonic patterns across Cloudflare primitives.

## Small pattern set to preserve

| Pattern | Meaning | Examples |
|---|---|---|
| Service | Active wrapper around a binding or REST client. | `R2Bucket`, `D1Database`, `QueueService`, `WorkflowService` |
| Ref | Cheap handle to a named resource. | `R2ObjectRef`, `KVKey`, `DurableObjectRef`, `WorkflowInstance` |
| Request | Dataclass input shape. | `VectorQuery`, `TextGenerationRequest`, `ChatRequest` |
| Result | Dataclass output shape. | `WorkflowStatus`, `QueueBatchResult`, `ChatResponse` |
| Progress | Known-size operation state. | `Progress` |
| Checkpoint | Resumable stream/import state. | `Checkpoint` |
| Event | Ordered operational events in examples until a shared type is justified. | example-local event dataclasses |
| Demo transport | Deterministic local substitute. | `DemoAIService`, `DemoAIGateway`, `DemoVectorIndex` |
| Raw escape | Access to the platform object. | `.raw` |

## Example ideas

### 1. Workflows timeline with D1

Path:

```text
POST /start
GET /status/<id>
GET /timeline/<id>
```

Primitives:

```text
Workflows + D1 + xampler.status
```

What it proves:

- durable step state;
- visible progress;
- timeline route pattern;
- route-level verifier can assert step order and final state.

Potential API learned:

```python
@dataclass(frozen=True)
class ImportEvent:
    name: str
    state: OperationState
    details: dict[str, object] | None = None
```

### 2. Queue retry dashboard

Path:

```text
POST /jobs
GET /jobs/status
POST /dev/reset
```

Primitives:

```text
Queues + Durable Object tracker + optional D1 history
```

What it proves:

- retry/backoff counts;
- dead-letter visibility;
- better operational assertions than HTTP 202.

Verifier assertions:

```text
sent == processed + retried + dead_lettered (eventually)
dead_lettered >= 1 for deterministic failing job
```

### 3. Browser Rendering report verifier

Path:

```text
GET /report
GET /screenshot?url=/report
GET /content?url=/report
GET /pdf?url=/report
GET /scrape?url=/report
```

Primitives:

```text
Browser Rendering + local fixture route
```

What it proves:

- same page through screenshot/content/PDF/scrape;
- content assertions are deterministic;
- paid remote verification is richer than “request succeeded.”

### 4. R2 Data Catalog schema lifecycle

Path:

```text
POST /lifecycle/<namespace>/<table>
GET /schema/<namespace>/<table>
GET /timeline/<namespace>/<table>
```

Primitives:

```text
R2 Data Catalog + R2 + D1 optional metadata cache
```

What it proves:

- namespace/table lifecycle;
- schema payload shape;
- cleanup correctness.

### 5. Email policy router with fixtures

Path:

```text
POST /fixtures/email/allow
POST /fixtures/email/reject
POST /fixtures/email/annotate
```

Primitives:

```text
Email Workers policy shape + fixture events
```

What it proves:

- decision API is independent of runtime event;
- policy can be unit-tested;
- route verifier can assert allow/reject/forward decisions.

### 6. HTMLRewriter extractor fixtures

Path:

```text
GET /fixture/page
GET /extract/opengraph
GET /rewrite/opengraph
```

Primitives:

```text
HTMLRewriter-shaped API + fixture HTML
```

What it proves:

- escaped metadata;
- extractor and rewriter shapes;
- later migration path to platform HTMLRewriter callbacks.

### 7. Durable Object room presence and replay

Path:

```text
/ws/rooms/<room>
GET /rooms/<room>/status
GET /rooms/<room>/timeline
GET /rooms/<room>/replay
```

Primitives:

```text
Durable Objects + WebSockets + R2/D1 transcript export
```

What it proves:

- stateful coordination;
- reconnect/presence observability;
- transcript checkpointing.

## API improvements to consider

### Example-local operational events

Keep timeline-shaped operational events local until multiple examples prove one shared type.

Why: Workflows, Queues, Durable Objects, Gutenberg, and HVSC all need visible operational events, but a shared operations or pipeline module would be premature before route-level examples converge.

### `xampler.testing`

Candidate helpers:

```python
FakeResponse
FakeQueueMessage
FakeD1Statement
FakeKVBinding
```

Why: docs and tests already repeat small fakes. Keep these explicitly test-only so runtime code stays lean.

## Rules for adding API

1. Add a fake/demo-backed unit test first.
2. Use the new API in at least one executable example.
3. Prefer dataclasses over dict conventions.
4. Preserve product names: D1, R2, Queue, Workflow, Durable Object.
5. Keep `.raw` for escape hatches.
6. Do not add a global Cloudflare client yet.
