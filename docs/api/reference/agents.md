# Agents

## Import

```python
from xampler.agents import AgentMessage, AgentSession, DemoAgent
```

## Copy this API

```python
result = await DemoAgent().run("Find matching docs")
```

## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
