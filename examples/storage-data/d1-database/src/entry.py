from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import parse_qs, urlparse

from xampler.d1 import D1Database
from xampler.response import json_response

try:
    from workers import WorkerEntrypoint  # type: ignore[import-not-found]
except ImportError:

    class WorkerEntrypoint:  # type: ignore[no-redef]
        env: Any = None


@dataclass(frozen=True)
class Quote:
    quote: str
    author: str


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Any:
        db = D1Database(self.env.DB)
        url = urlparse(str(request.url))

        if url.path == "/by-author":
            author = parse_qs(url.query).get("author", ["PEP 20"])[0]
            quote = await db.statement(
                "SELECT quote, author FROM quotes WHERE author = ? LIMIT 1"
            ).one_as(Quote, author)
            return json_response(
                asdict(quote) if quote else {"error": "not found"},
                status=200 if quote else 404,
            )

        if url.path == "/explain":
            author = parse_qs(url.query).get("author", ["PEP 20"])[0]
            plan = await db.statement(
                "EXPLAIN QUERY PLAN SELECT quote, author "
                "FROM quotes INDEXED BY idx_quotes_author WHERE author = ?"
            ).all(author)
            return json_response({"plan": plan})

        quote = await db.statement(
            "SELECT quote, author FROM quotes ORDER BY RANDOM() LIMIT 1"
        ).one_as(Quote)
        return json_response(asdict(quote or Quote("No quotes yet", "D1")))
