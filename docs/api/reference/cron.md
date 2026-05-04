# Cron

Experimental surface: currently event/result types plus a demo scheduled job, not a full binding wrapper.

## Import

```python
from xampler.experimental.cron import ScheduledEventInfo, DemoScheduledJob
```

## Copy this API

```python
info = ScheduledEventInfo.from_event(event)
result = await DemoScheduledJob().run(info)
```

## Testability

Use fake bindings for binding-backed services and explicit `Demo*` clients for account-backed services. See [testability](../testability.md).
