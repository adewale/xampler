# Scheduled 08 — Cron

A scheduled Worker with a small `ScheduledJob` service object. Test with `/cdn-cgi/handler/scheduled`.

## Cloudflare docs

- [Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/)

## Copy this API

```python
from xampler.cron import DemoScheduledJob, ScheduledEventInfo

result = await DemoScheduledJob().run(ScheduledEventInfo.from_event(event))
```
