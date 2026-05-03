# Testability and red-green-refactor TDD

Xampler is designed so reusable Cloudflare API shape can be developed with a normal red-green-refactor loop.

## The loop

```text
Red      write a failing unit test against xampler/* with a fake binding or Demo* client
Green    implement the smallest wrapper behavior in xampler/*
Refactor update an executable example so route code imports the library API
Verify   run pyright, pytest, and optionally xc verify / xc remote verify
```

Recommended commands:

```bash
uv run ruff check .
uv run pyright
uv run pyright -p pyright.examples.json
uv run pytest -q
xc verify r2
```

Remote checks are optional and explicit:

```bash
xc remote prepare vectorize
xc remote verify vectorize
xc remote cleanup vectorize
```

## Why Xampler is testable

| Design choice | TDD benefit |
|---|---|
| Small importable modules under `xampler/` | Unit tests can target the API without starting Wrangler. |
| Wrappers accept raw bindings/clients | Tests can pass tiny fakes instead of mocking the whole runtime. |
| `.raw` remains public | Tests cover the Pythonic contract while advanced platform behavior can escape to Cloudflare objects. |
| Dataclass request/result types | Expected values are simple to construct and assert. |
| Explicit `Demo*` transports | Account-backed products stay deterministic locally. |
| Examples import the library | Refactors are proven in realistic Worker route code. |
| Local/remote lifecycle split | Fast TDD stays local; paid/deployed checks stay opt-in. |
| Strict `pyright` | Type feedback catches API-design mistakes before runtime. |

## Pattern: fake a binding

```python
import pytest
from xampler.kv import KVNamespace

class FakeKVBinding:
    def __init__(self):
        self.values = {}

    async def get(self, key):
        return self.values.get(key)

    async def put(self, key, value, options=None):
        self.values[key] = value

    async def delete(self, key):
        self.values.pop(key, None)

@pytest.mark.asyncio
async def test_kv_read_write_json():
    kv = KVNamespace(FakeKVBinding())
    key = kv.key("profile:ada")

    await key.write_json({"name": "Ada"})

    assert await key.read_json() == {"name": "Ada"}
```

## Pattern: use a Demo transport

```python
import pytest
from xampler.ai_gateway import ChatMessage, ChatRequest, DemoAIGateway

@pytest.mark.asyncio
async def test_gateway_shape_without_remote_credentials():
    gateway = DemoAIGateway()
    result = await gateway.chat(ChatRequest(messages=[ChatMessage("user", "hello")]))

    assert "hello" in result.text
    assert result.raw["xampler"]["source"] == "demo-ai-gateway"
```

## Pattern: keep routes thin

Good examples keep reusable behavior in `xampler/` and route-specific behavior in `examples/`:

```python
from xampler.workflows import WorkflowService
from xampler.response import json_response

async def fetch(request):
    workflow = WorkflowService(env.PIPELINE)
    started = await workflow.start()
    return json_response(started)
```

Test the wrapper directly with fakes. Verify the route with `xc verify <example>`.

## What not to test locally

Do not pretend paid Cloudflare products ran locally. Use one of these instead:

1. A `Demo*` client for deterministic local behavior.
2. A fake binding that models only the method you need.
3. An opt-in `xc remote verify ...` profile for deployed behavior.

This keeps tests honest and cheap.

## Current weak spots

TDD is strongest for R2, D1, KV, Queues, Vectorize, Workers AI, Workflows, Durable Object refs, Cron, response helpers, and streaming helpers.

It is weaker where realism still depends on external setup: Hyperdrive, Browser Rendering beyond deterministic checks, R2 Data Catalog append/read, real Agents SDK interop, and advanced Durable Object/WebSocket hibernation semantics.
