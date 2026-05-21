# Agents

## Import

```python
from xampler.agents import AgentMessage, AgentSession, DemoAgent
```

## Copy this API

```python
result = await DemoAgent().run("Find matching docs")
```

## Capability table

| Operation | Status | Notes |
|---|---|---|
| Deterministic agent run | Demo-only | `DemoAgent` verifies message/result shape locally without a provider. |
| `AgentSession.run()` wrapper | Caveated | Wraps a raw session object; direct Cloudflare Agents SDK interop is still evolving. |
| Streaming responses and human approval state | Not covered | Future work after runtime support stabilizes. |


## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
