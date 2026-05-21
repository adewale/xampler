# WebSockets

Experimental surface: currently status/message dataclasses plus a demo session, not a full WebSocket binding/session wrapper.

## Import

```python
from xampler.experimental.websockets import DemoWebSocketSession, WebSocketStatus
```

## Copy this API

```python
status = await DemoWebSocketSession().status()
```

## Capability table

| Operation | Status | Notes |
|---|---|---|
| Demo WebSocket status | Demo-only | Local tests validate status shape. |
| Durable Object chatroom broadcast | Remote-only | Prepared `websockets` profile verifies deployed two-client broadcast. |
| Outbound stream reconnect state | Caveated | Deterministic status seam exists; richer fake stream pending. |


## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
