from __future__ import annotations

import html
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, cast
from urllib.parse import parse_qs, quote, unquote, urlparse

import js  # type: ignore[import-not-found]
from cfboundary.ffi import to_js
from workers import Response, WorkerEntrypoint  # type: ignore[import-not-found]

from xampler.d1 import D1Database
from xampler.response import html_response, json_response, text_response

SLUG_RE = re.compile(r"^[A-Z][A-Za-z0-9]{2,63}$")
WIKI_WORD_RE = re.compile(r"\b[A-Z][a-z0-9]+[A-Z][A-Za-z0-9]*\b")


@dataclass(frozen=True)
class WikiPage:
    slug: str
    title: str
    body: str
    current_revision: int
    updated_at: str


@dataclass(frozen=True)
class WikiRevision:
    slug: str
    revision: int
    title: str
    body: str
    author: str | None
    message: str | None
    created_at: str


@dataclass(frozen=True)
class WikiSearchResult:
    slug: str
    title: str
    snippet: str


class Wiki:
    def __init__(self, db: D1Database):
        self.db = db

    async def get_page(self, slug: str) -> WikiPage | None:
        row = await self.db.query_one(
            "SELECT slug, title, body, current_revision, updated_at FROM pages WHERE slug = ?",
            slug,
        )
        return None if row is None else WikiPage(**row)

    async def recent(self, limit: int = 20) -> list[WikiPage]:
        rows = await self.db.query(
            """
            SELECT slug, title, body, current_revision, updated_at
            FROM pages
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            limit,
        )
        return [WikiPage(**row) for row in rows]

    async def history(self, slug: str) -> list[WikiRevision]:
        rows = await self.db.query(
            """
            SELECT slug, revision, title, body, author, message, created_at
            FROM revisions
            WHERE slug = ?
            ORDER BY revision DESC
            """,
            slug,
        )
        return [WikiRevision(**row) for row in rows]

    async def save_page(
        self,
        *,
        slug: str,
        title: str,
        body: str,
        author: str | None = None,
        message: str | None = None,
        base_revision: int | None = None,
    ) -> WikiPage:
        validate_slug(slug)
        now = datetime.now(UTC).isoformat()
        existing = await self.get_page(slug)
        if (
            existing is not None
            and base_revision is not None
            and existing.current_revision != base_revision
        ):
            raise ValueError("edit conflict: page changed before this save")
        revision = 1 if existing is None else existing.current_revision + 1
        if existing is None:
            await self.db.statement(
                """
                INSERT INTO pages (slug, title, body, current_revision, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """
            ).run(slug, title, body, revision, now)
        else:
            await self.db.statement(
                """
                UPDATE pages
                SET title = ?, body = ?, current_revision = ?, updated_at = ?
                WHERE slug = ?
                """
            ).run(title, body, revision, now, slug)
        await self.db.statement(
            """
            INSERT INTO revisions (slug, revision, title, body, author, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
        ).run(slug, revision, title, body, author, message, now)
        row = await self.db.query_one("SELECT id FROM pages WHERE slug = ?", slug)
        page_id = int(row["id"]) if row else revision
        await self.db.statement("DELETE FROM page_search WHERE page_id = ?").run(page_id)
        await self.db.statement(
            "INSERT INTO page_search (page_id, slug, title, body) VALUES (?, ?, ?, ?)"
        ).run(page_id, slug, title, body)
        page = await self.get_page(slug)
        if page is None:  # pragma: no cover - defensive guard for impossible write failure.
            raise RuntimeError("page was not saved")
        return page

    async def search(self, query: str) -> list[WikiSearchResult]:
        safe_query = " ".join(token for token in re.findall(r"[A-Za-z0-9]+", query) if token)
        if not safe_query:
            return []
        rows = await self.db.query(
            """
            SELECT slug, title, snippet(page_search, 3, '<mark>', '</mark>', '…', 12) AS snippet
            FROM page_search
            WHERE page_search MATCH ?
            ORDER BY rank
            LIMIT 20
            """,
            safe_query,
        )
        return [WikiSearchResult(**row) for row in rows]

    async def record_event(self, event_name: str, route: str, method: str) -> None:
        await self.db.statement(
            """
            INSERT INTO wide_events (event_name, route, method, dimensions, created_at)
            VALUES (?, ?, ?, ?, ?)
            """
        ).run(
            event_name,
            route,
            method,
            json.dumps({"route": route, "method": method, "app": "mini-wiki"}),
            datetime.now(UTC).isoformat(),
        )

    async def wide_events(self) -> list[dict[str, Any]]:
        return await self.db.query(
            """
            SELECT event_name, route, method, dimensions, created_at
            FROM wide_events
            ORDER BY id DESC
            LIMIT 25
            """
        )

    async def export_revisions(self) -> str:
        rows = await self.db.query(
            """
            SELECT slug, revision, title, body, author, message, created_at
            FROM revisions
            ORDER BY slug, revision
            """
        )
        return "\n".join(json.dumps(row, separators=(",", ":")) for row in rows) + "\n"


def validate_slug(slug: str) -> None:
    if not SLUG_RE.fullmatch(slug):
        raise ValueError("slugs must be WikiWords like HomePage or PythonWorkers")


def wiki_title(slug: str) -> str:
    return re.sub(r"(?<!^)([A-Z])", r" \1", slug).strip()


def shell(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} · Mini Wiki</title>
  <link rel="stylesheet" href="/style.css">
</head>
<body>
  <header>
    <h1><a href="/">Mini Wiki</a></h1>
    <nav>
      <a href="/wiki/HomePage">HomePage</a>
      <a href="/recent">Recent</a>
      <a href="/search">Search</a>
      <a href="/export.jsonl">Export</a>
    </nav>
  </header>
  {body}
</body>
</html>"""


def render_markup(text: str) -> str:
    escaped = html.escape(text)
    paragraphs: list[str] = []
    in_code = False
    code_lines: list[str] = []
    for raw_line in escaped.splitlines():
        line = raw_line.rstrip()
        if line.startswith("```"):
            if in_code:
                paragraphs.append(f"<pre>{'\n'.join(code_lines)}</pre>")
                code_lines = []
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(line)
        elif line.startswith("# "):
            paragraphs.append(f"<h2>{link_wiki_words(line[2:])}</h2>")
        elif line:
            paragraphs.append(f"<p>{link_wiki_words(line)}</p>")
    if code_lines:
        paragraphs.append(f"<pre>{'\n'.join(code_lines)}</pre>")
    return "\n".join(paragraphs) or "<p class='muted'>Empty page.</p>"


def link_wiki_words(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        slug = match.group(0)
        return f'<a href="/wiki/{quote(slug)}">{slug}</a>'

    return WIKI_WORD_RE.sub(replace, text)


def redirect(location: str, status: int = 303) -> Response:
    return Response("", status=status, headers={"location": location})  # type: ignore[call-arg]


async def form_data(request: Any) -> dict[str, str]:
    raw = parse_qs(str(await request.text()), keep_blank_values=True)
    return {key: values[0] if values else "" for key, values in raw.items()}


class Default(WorkerEntrypoint):
    async def fetch(self, request: Any) -> Response:
        parsed = urlparse(str(request.url))
        path = parsed.path.rstrip("/") or "/"
        wiki = Wiki(D1Database(self.env.DB))
        await wiki.record_event("http.request", path, str(request.method))
        try:
            if path == "/events":
                return Response.json({"events": await wiki.wide_events()})
            if path.startswith("/cached/wiki/"):
                slug = unquote(path.removeprefix("/cached/wiki/"))
                return await cached_wiki_page(wiki, slug)
            if path == "/":
                return await recent_page(wiki)
            if path == "/recent":
                return await recent_page(wiki)
            if path == "/search":
                query = parse_qs(parsed.query).get("q", [""])[0]
                return await search_page(wiki, query)
            if path == "/export.jsonl":
                return text_response(await wiki.export_revisions())
            if path.startswith("/wiki/"):
                return await wiki_route(wiki, request, path)
            return html_response(shell("Not found", "<p>Not found.</p>"), status=404)
        except ValueError as exc:
            body = f"<p>{html.escape(str(exc))}</p>"
            return html_response(shell("Bad request", body), status=400)


async def cached_wiki_page(wiki: Wiki, slug: str) -> Response:
    validate_slug(slug)
    cache = cast(Any, js).caches.default
    cache_url = f"https://mini-wiki.local/wiki/{quote(slug)}"
    cached = await cache.match(cache_url)
    if cached:
        text = str(await cached.text())
        response_cls = cast(Any, Response)
        return response_cls(
            text,
            status=200,
            headers={"content-type": "text/html; charset=utf-8", "x-wiki-cache": "HIT"},
        )
    page = await wiki.get_page(slug)
    if page is None:
        return await show_page(wiki, slug)
    page_body = (
        f"<h2>{html.escape(page.title)}</h2>"
        f"<article class='page'>{render_markup(page.body)}</article>"
    )
    body = shell(page.title, page_body)
    await cache.put(
        cache_url,
        cast(Any, js).Response.new(
            body,
            to_js({"headers": {"content-type": "text/html; charset=utf-8"}}),
        ),
    )
    response_cls = cast(Any, Response)
    return response_cls(
        body,
        status=200,
        headers={"content-type": "text/html; charset=utf-8", "x-wiki-cache": "MISS"},
    )


async def recent_page(wiki: Wiki) -> Response:
    pages = await wiki.recent()
    if not pages:
        body = """
        <p>No pages yet. Start with <a href="/wiki/HomePage/edit">HomePage</a>.</p>
        <form action="/search"><input name="q" placeholder="Search"><button>Search</button></form>
        """
    else:
        items = "".join(
            f'<li><a href="/wiki/{quote(page.slug)}">{html.escape(page.title)}</a> '
            f'<span class="muted">r{page.current_revision} · '
            f"{html.escape(page.updated_at)}</span></li>"
            for page in pages
        )
        search_form = (
            "<form action='/search'><input name='q' placeholder='Search'>"
            "<button>Search</button></form>"
        )
        body = f"<h2>Recent pages</h2><ul>{items}</ul>{search_form}"
    return html_response(shell("Recent", body))


async def search_page(wiki: Wiki, query: str) -> Response:
    results = await wiki.search(query) if query else []
    items = "".join(
        f'<li><a href="/wiki/{quote(result.slug)}">{html.escape(result.title)}</a>'
        f"<br>{result.snippet}</li>"
        for result in results
    )
    form = (
        f"<form action='/search'><input name='q' value='{html.escape(query)}' "
        "placeholder='Search'><button>Search</button></form>"
    )
    body = f"{form}<h2>Search results</h2><ul>{items}</ul>"
    return html_response(shell("Search", body))


async def wiki_route(wiki: Wiki, request: Any, path: str) -> Response:
    rest = path.removeprefix("/wiki/")
    parts = rest.split("/")
    slug = unquote(parts[0])
    validate_slug(slug)
    action = parts[1] if len(parts) > 1 else "show"
    if request.method == "POST" and action == "show":
        data = await form_data(request)
        page = await wiki.save_page(
            slug=slug,
            title=data.get("title") or wiki_title(slug),
            body=data.get("body", ""),
            author=data.get("author") or None,
            message=data.get("message") or None,
            base_revision=int(data["base_revision"]) if data.get("base_revision") else None,
        )
        return redirect(f"/wiki/{quote(page.slug)}")
    if action == "edit":
        return await edit_page(wiki, slug)
    if action == "history":
        return await history_page(wiki, slug)
    if action == "raw":
        page = await wiki.get_page(slug)
        if page is None:
            return text_response("not found", status=404)
        return text_response(page.body)
    if action == "json":
        page = await wiki.get_page(slug)
        if page is None:
            return json_response({"error": "not found"}, status=404)
        return json_response(asdict(page))
    return await show_page(wiki, slug)


async def show_page(wiki: Wiki, slug: str) -> Response:
    page = await wiki.get_page(slug)
    if page is None:
        body = (
            f"<h2>{html.escape(slug)}</h2><p>This page does not exist yet. "
            f'<a class="missing" href="/wiki/{quote(slug)}/edit">'
            f"Create {html.escape(slug)}?</a></p>"
        )
        return html_response(shell(slug, body), status=404)
    links = (
        f"<p><a href='/wiki/{quote(slug)}/edit'>Edit</a> · "
        f"<a href='/wiki/{quote(slug)}/history'>History</a> · "
        f"<a href='/wiki/{quote(slug)}/raw'>Raw</a></p>"
    )
    body = (
        f"<h2>{html.escape(page.title)}</h2>"
        f"<p class='muted'>Revision {page.current_revision} · "
        f"{html.escape(page.updated_at)}</p>"
        f"{links}<article class='page'>{render_markup(page.body)}</article>"
    )
    return html_response(shell(page.title, body))


async def edit_page(wiki: Wiki, slug: str) -> Response:
    page = await wiki.get_page(slug)
    title = page.title if page else wiki_title(slug)
    body_text = page.body if page else f"# {title}\n\nDescribe {slug} here. Link to HomePage."
    revision = page.current_revision if page else 0
    form = f"""
    <h2>Edit {html.escape(slug)}</h2>
    <form method="post" action="/wiki/{quote(slug)}">
      <input type="hidden" name="base_revision" value="{revision}">
      <label>Title <input name="title" value="{html.escape(title)}"></label>
      <label>Body <textarea name="body">{html.escape(body_text)}</textarea></label>
      <label>Author <input name="author" value="Pythonista"></label>
      <label>Message <input name="message" value="edit {html.escape(slug)}"></label>
      <button>Save revision</button>
    </form>
    """
    return html_response(shell(f"Edit {slug}", form))


async def history_page(wiki: Wiki, slug: str) -> Response:
    revisions = await wiki.history(slug)
    items = "".join(
        f"<li>r{rev.revision}: {html.escape(rev.title)} — {html.escape(rev.created_at)} "
        f"<span class='muted'>{html.escape(rev.message or '')}</span></li>"
        for rev in revisions
    )
    body = f"<h2>History for {html.escape(slug)}</h2><ul>{items}</ul>"
    return html_response(shell(f"History {slug}", body))
