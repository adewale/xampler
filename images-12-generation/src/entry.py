from io import BytesIO

from PIL import Image
from workers import Response, WorkerEntrypoint


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        img = Image.new("RGB", (300, 120), "#2563eb")
        out = BytesIO()
        img.save(out, format="PNG")
        return Response(out.getvalue(), headers={"content-type": "image/png"})
