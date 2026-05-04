# Protocols in Xampler

Xampler uses Python `Protocol` types for **capabilities**, not product identity.

The key rule:

```text
Real services and Demo services should usually be siblings that satisfy the same Protocol,
not parent/child classes.
```

## Why Protocols instead of inheritance?

A real Xampler service usually wraps a Cloudflare binding or REST credential:

```python
AIService(env.AI)
AIGateway(account_id=..., gateway_id=..., api_key=...)
VectorIndex(env.INDEX)
```

A demo service is deterministic and local:

```python
DemoAIService()
DemoAIGateway()
DemoVectorIndex()
```

A demo is not actually the real Cloudflare product. It does not have the same runtime, credentials, latency, failure modes, billing behavior, metadata, or `.raw` object. Making demos subclass real services would make this misleading:

```python
isinstance(DemoAIGateway(), AIGateway)  # We generally do not want this.
```

Instead, both should satisfy the same small capability Protocol when app code needs substitutability.

## Capability Protocol example

```python
from typing import Protocol

from xampler.ai import AIService, DemoAIService, TextGenerationRequest, TextGenerationResponse


class SupportsTextGeneration(Protocol):
    async def generate_text(
        self, request: TextGenerationRequest
    ) -> TextGenerationResponse: ...


async def summarize(ai: SupportsTextGeneration, text: str) -> str:
    result = await ai.generate_text(TextGenerationRequest(f"Summarize: {text}"))
    return result.text


# Real Cloudflare path.
summary = await summarize(AIService(env.AI), "...")

# Local deterministic path.
summary = await summarize(DemoAIService(), "...")
```

The app depends on a capability:

```text
generate_text(request) -> response
```

not on whether the implementation is real or demo.

## When to use concrete classes

Use concrete product classes at the Cloudflare boundary:

```python
bucket = R2Bucket(env.BUCKET)
db = D1Database(env.DB)
queue = QueueService(env.JOBS)
```

Concrete classes are best when code needs product-specific vocabulary:

```python
await bucket.object("notes/a.txt").write_text("hello")
await db.statement("SELECT * FROM quotes").one()
await queue.send(QueueJob("index", {"key": "notes/a.txt"}))
```

## When to use Protocols

Use Protocols at composition boundaries, especially when both real and demo implementations should work:

```python
class SupportsChat(Protocol):
    async def chat(self, request: ChatRequest) -> ChatResponse: ...
```

Good Protocol candidates:

| Capability | Real implementation | Demo implementation |
|---|---|---|
| Text generation | `AIService` | `DemoAIService` |
| Chat gateway | `AIGateway` | `DemoAIGateway` |
| Vector search | `VectorIndex` | `DemoVectorIndex` |
| SQL query | `R2SqlClient` | `DemoR2SqlClient` |
| Catalog lifecycle | `R2DataCatalog` | `DemoR2DataCatalog` |
| Workflow start/status | `WorkflowService` | `DemoWorkflowService` |
| Postgres query shape | `HyperdrivePostgres` | `DemoPostgres` |

## Current Protocol inventory

This is the complete current inventory of Protocol use in the shared package and executable examples.

| Protocol | Location | Scope | Rationale |
|---|---|---|---|
| `SupportsRaw` | `xampler.types` | Shared library | Marks objects that expose a `.raw` platform escape hatch without requiring inheritance from `CloudflareService` or `ResourceRef`. It is `@runtime_checkable` because checking for the escape hatch can be useful in generic tooling/tests. |
| `DemoTransport[RequestT, ResultT]` | `xampler.types` | Shared library | Describes deterministic local transports that accept a typed request and return a typed result. `DemoAIService` implements this for text generation. It captures the demo convention without making demos inherit real services. |
| `RemoteVerifier` | `xampler.types` | Shared library | Describes verifier-style objects that can prove remote behavior with `verify_remote() -> JsonObject`. It keeps verification as a capability separate from product wrappers. |
| `ScheduledJob` | `xampler.experimental.cron` | Shared library | Describes cron job implementations with `run(ScheduledEventInfo) -> ScheduledRunResult`. The Worker scheduled handler can depend on this capability while tests use `DemoScheduledJob`. |
| `QueueEventRecorder` | `xampler.queues` | Shared library | Describes optional queue observability sinks with `record(kind, body)`. A recorder may be backed by a Durable Object, D1, logs, or tests; it is deliberately not a Queue namespace/ref API. |
| `AgentTool` | `examples/ai-agents/agents-sdk-tools/src/entry.py` | Example-local | Describes tool objects that have a `name` and async `run(**kwargs)`. It lets `DemoAgent` accept any tool with the right capability without introducing an Agents inheritance hierarchy before the API shape is stable. |
| `Runnable` | `examples/ai-agents/langchain-style-chain/src/entry.py` | Example-local | Mirrors LangChain's Runnable idea with `invoke(PromptInput) -> PromptOutput`. It keeps package-orchestration code swappable while avoiding a hard dependency on LangChain runtime behavior inside Workers. |

### Shared Protocols

`xampler.types` contains the general-purpose Protocols:

```python
from xampler.types import DemoTransport, RemoteVerifier, SupportsRaw
```

They are intentionally small. Do not build a large inheritance framework around them.

### Product-local Protocols

`xampler.experimental.cron.ScheduledJob` is product-local because the capability is specific and stable: a scheduled event becomes a scheduled run result.

### Example-local Protocols

`AgentTool` and `Runnable` stay in examples because they are still abstraction research. If two or more examples need the same capability shape, promote the Protocol into `xampler/` with direct tests and docs.

## What not to do

Do not make demo services inherit real services just to satisfy a type checker:

```python
class DemoAIGateway(AIGateway):  # Avoid.
    ...
```

Problems this creates:

1. The demo has no real account/gateway/provider credentials.
2. `.raw` semantics become muddy.
3. Inherited methods may accidentally call real runtime code.
4. The type suggests behavior equivalence that does not exist.
5. Constructor special cases start leaking through the API.

## Fake bindings vs Demo services

Use fake bindings when testing wrapper behavior:

```python
db = D1Database(FakeD1Binding())
```

Use Demo services when testing application flow without credentials:

```python
gateway = DemoAIGateway()
result = await gateway.chat(ChatRequest(messages=[ChatMessage("user", "hello")]))
```

Use remote verification when proving Cloudflare actually did the work:

```bash
xc remote verify ai-gateway
```

## Rule of thumb

```text
Concrete class at the product boundary.
Protocol at the composition boundary.
Demo class for deterministic local behavior.
Fake binding for wrapper tests.
Remote verifier for real Cloudflare behavior.
```

This keeps Xampler Pythonic, testable, and honest about what ran locally versus what ran on Cloudflare.
