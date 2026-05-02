from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol

from workers import Response, WorkerEntrypoint


@dataclass(frozen=True)
class PromptInput:
    topic: str
    audience: str = "Python developers"


@dataclass(frozen=True)
class PromptOutput:
    prompt: str
    answer: str
    steps: list[str]


class Runnable(Protocol):
    async def invoke(self, value: PromptInput) -> PromptOutput: ...


class PromptTemplate:
    def format(self, value: PromptInput) -> str:
        return f"Explain {value.topic} to {value.audience} in one practical sentence."


class DemoModel:
    async def complete(self, prompt: str) -> str:
        return f"LangChain-compatible LCEL demo: {prompt}"


class PromptChain:
    def __init__(self, template: PromptTemplate, model: DemoModel):
        self.template = template
        self.model = model
        self.raw = {"template": template, "model": model}

    async def invoke(self, value: PromptInput) -> PromptOutput:
        prompt = self.template.format(value)
        answer = await self.model.complete(prompt)
        return PromptOutput(prompt=prompt, answer=answer, steps=["template", "model"])


class PromptService:
    def __init__(self, chain: Runnable):
        self.chain = chain

    async def answer(self, topic: str) -> PromptOutput:
        return await self.chain.invoke(PromptInput(topic=topic))


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        service = PromptService(PromptChain(PromptTemplate(), DemoModel()))
        result = await service.answer("Cloudflare Python Workers")
        return Response.json(asdict(result))
