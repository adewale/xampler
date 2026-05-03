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

## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
