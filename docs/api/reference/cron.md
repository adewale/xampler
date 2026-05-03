# Cron

## Import

```python
from xampler.cron import ScheduledEventInfo, DemoScheduledJob
```

## Copy this API

```python
info = ScheduledEventInfo.from_event(event)
result = await DemoScheduledJob().run(info)
```

## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
