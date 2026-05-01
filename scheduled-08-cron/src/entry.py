from workers import Response, WorkerEntrypoint


class ScheduledJob:
    async def run(self, cron: str) -> str:
        return f"ran scheduled job for {cron}"

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return Response("scheduled worker is alive")
    async def scheduled(self, event, env, ctx):
        print(await ScheduledJob().run(str(event.cron)))
