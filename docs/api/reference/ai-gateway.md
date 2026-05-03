# AI Gateway

## Import

```python
from xampler.ai_gateway import AIGateway, ChatMessage, ChatRequest, ChatResponse, DemoAIGateway
```

## Copy this API

```python
gateway = AIGateway(account_id=account_id, gateway_id=gateway_id, api_key=api_key)
result = await gateway.chat(ChatRequest(messages=[ChatMessage("user", "hello")]))
print(result.text)
```

## Main classes

- `ChatMessage(role, content)` models OpenAI-compatible chat messages.
- `ChatRequest(messages, model="openai/gpt-4o-mini")` is the request envelope.
- `ChatResponse(text, raw)` preserves parsed text and raw provider response.
- `AIGateway` calls the Cloudflare AI Gateway OpenAI-compatible endpoint.
- `DemoAIGateway` returns deterministic local responses.

## Credentials

Remote checks need:

```text
CLOUDFLARE_ACCOUNT_ID
CLOUDFLARE_API_TOKEN
XAMPLER_AI_GATEWAY_ID
OPENAI_API_KEY
```

Optional model override:

```text
XAMPLER_AI_GATEWAY_MODEL=openai/gpt-4o-mini
```

Use a small supported model for routine verification to keep provider cost low.

## Testability

Use `DemoAIGateway` for local tests. Assert `ChatResponse.text` for app behavior and inspect `.raw` only when testing provider/gateway metadata.
