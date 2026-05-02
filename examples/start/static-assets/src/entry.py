from workers import Response, WorkerEntrypoint


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return Response("Dynamic Python route. Static files are served by Assets.")
