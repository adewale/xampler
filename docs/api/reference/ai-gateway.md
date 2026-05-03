# AI Gateway

## Import

```python
from xampler.ai_gateway import AIGateway, ChatMessage, ChatRequest
```

## Copy this API

```python
gateway = AIGateway(account_id=account_id, gateway_id=gateway_id, api_key=api_key)
result = await gateway.chat(ChatRequest(messages=[ChatMessage("user", "hello")]))
```

## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
