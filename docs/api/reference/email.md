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

## Testability

Use fixture `IncomingEmail` values for allow/reject/forward policy tests before wiring real Email Routing events.
