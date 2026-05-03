# AI Gateway 20 — Universal Gateway

Calls AI Gateway OpenAI-compatible endpoint. Set `ACCOUNT_ID`, `GATEWAY_ID`, and secret `OPENAI_API_KEY`.

## Cloudflare docs

- [AI Gateway](https://developers.cloudflare.com/ai-gateway/)

## Copy this API

```python
from xampler.ai_gateway import AIGateway, ChatMessage, ChatRequest

gateway = AIGateway(account_id=account_id, gateway_id=gateway_id, api_key=api_key)
result = await gateway.chat(ChatRequest(messages=[ChatMessage("user", "hello")]))
```
