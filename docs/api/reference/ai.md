# Workers AI

## Import

```python
from xampler.ai import AIService, TextGenerationRequest
```

## Copy this API

```python
ai = AIService(env.AI)
result = await ai.generate_text(TextGenerationRequest("Summarize this"))
```

## Capability table

| Operation | Status | Notes |
|---|---|---|
| Text generation request/result shape | Caveated | Local examples use deterministic demos; prepared remote profile calls real Workers AI. |
| Image/audio/embedding tasks | Not covered | Use `.raw` or add task-specific helpers later. |
| Model catalog helpers | Not covered | Future wrapper work. |


## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
