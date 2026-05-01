from workers import Response, WorkerEntrypoint


class PromptService:
    def answer(self, prompt: str) -> str:
        return f"LangChain-compatible prompt boundary: {prompt}"

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return Response(PromptService().answer("hello"))
