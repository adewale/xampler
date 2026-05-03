# Workers AI 09 — Inference

Pythonic AI service wrapper with typed request/response shapes.

## Cloudflare docs

- [Workers AI](https://developers.cloudflare.com/workers-ai/)

## Copy this API

```python
from xampler.ai import AIService, TextGenerationRequest

ai = AIService(env.AI)
result = await ai.generate_text(TextGenerationRequest("Explain Workers"))
```
