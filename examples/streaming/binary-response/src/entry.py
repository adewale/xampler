from __future__ import annotations

import base64

from workers import Response, WorkerEntrypoint

PNG_1X1_BLUE = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADUlEQVR4nGNkYPj/HwADAgH/"
    "bc8U9wAAAABJRU5ErkJggg=="
)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return Response(PNG_1X1_BLUE, headers={"content-type": "image/png"})
