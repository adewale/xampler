# Email Workers

Experimental surface: currently message/decision types plus a policy router, not a full Email Routing binding wrapper.

## Import

```python
from xampler.experimental.email import EmailRouter, IncomingEmail
```

## Copy this API

```python
router = EmailRouter(forward_to="archive@example.net", blocked_domains={"blocked.test"})
decision = router.decide(IncomingEmail("ada@example.com", "inbox@example.net", "hi", 128))
```

## Capability table

| Operation | Status | Notes |
|---|---|---|
| Policy decision routing | Demo-only | HTTP/local tests verify inspect/forward/reject decisions. |
| Real Email Routing event | Remote-only | Deployed Email Routing verification is future work. |
| MIME parsing, replies, SendEmail binding | Not covered | Future examples. |


## Testability

Use fixture `IncomingEmail` values for allow/reject/forward policy tests before wiring real Email Routing events.
