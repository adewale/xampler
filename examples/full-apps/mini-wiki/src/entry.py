# ruff: noqa: E501
from __future__ import annotations

import difflib
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

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,79}$")
WIKI_LINK_RE = re.compile(r"\[\[([^\]\n]{1,80})\]\]")
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

    async def all_pages(self) -> list[WikiPage]:
        rows = await self.db.query(
            """
            SELECT slug, title, body, current_revision, updated_at
            FROM pages
            ORDER BY lower(title), slug
            """
        )
        return [WikiPage(**row) for row in rows]

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

    async def backlinks(self, slug: str) -> list[WikiPage]:
        pages = await self.all_pages()
        return [page for page in pages if slug in extract_links(page.body) and page.slug != slug]

    async def wanted_pages(self) -> list[tuple[str, int]]:
        existing = {page.slug for page in await self.all_pages()}
        counts: dict[str, int] = {}
        for page in await self.all_pages():
            for linked in extract_links(page.body):
                if linked not in existing:
                    counts[linked] = counts.get(linked, 0) + 1
        return sorted(counts.items(), key=lambda item: (-item[1], item[0]))

    async def revision(self, slug: str, revision: int) -> WikiRevision | None:
        row = await self.db.query_one(
            """
            SELECT slug, revision, title, body, author, message, created_at
            FROM revisions
            WHERE slug = ? AND revision = ?
            """,
            slug,
            revision,
        )
        return None if row is None else WikiRevision(**row)

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


def slugify(label: str) -> str:
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", label.strip())
    slug = re.sub(r"[^A-Za-z0-9]+", "-", spaced.lower()).strip("-")
    return slug or "page"


def validate_slug(slug: str) -> None:
    if not SLUG_RE.fullmatch(slug):
        raise ValueError("slugs must be lowercase words like home-page or python-workers")


def wiki_title(slug: str) -> str:
    return slug.replace("-", " ").title()


def shell(title: str, body: str, *, query: str = "") -> str:
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
    <form class="header-search" action="/search">
      <input name="q" value="{html.escape(query)}" placeholder="Search wiki">
    </form>
    <nav>
      <a href="/wiki/home-page">Home</a>
      <a href="/all">All pages</a>
      <a href="/recent-changes">Recent changes</a>
      <a href="/wanted">Wanted</a>
    </nav>
  </header>
  {body}
</body>
</html>"""

def extract_links(text: str) -> set[str]:
    links = {slugify(match.group(1)) for match in WIKI_LINK_RE.finditer(text)}
    masked = WIKI_LINK_RE.sub(" ", text)
    links.update(slugify(match.group(0)) for match in WIKI_WORD_RE.finditer(masked))
    return links


def render_inline(text: str) -> str:
    escaped = html.escape(text)

    def bracket(match: re.Match[str]) -> str:
        label = html.unescape(match.group(1)).strip()
        slug = slugify(label)
        return f'<a href="/wiki/{quote(slug)}">{html.escape(label)}</a>'

    linked = WIKI_LINK_RE.sub(bracket, escaped)

    def wiki_word(match: re.Match[str]) -> str:
        label = match.group(0)
        slug = slugify(label)
        return f'<a href="/wiki/{quote(slug)}">{label}</a>'

    return WIKI_WORD_RE.sub(wiki_word, linked)


def render_markup(text: str) -> str:
    paragraphs: list[str] = []
    in_code = False
    in_list = False
    code_lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.rstrip()
        if stripped.startswith("```"):
            if in_list:
                paragraphs.append("</ul>")
                in_list = False
            if in_code:
                paragraphs.append(f"<pre>{'\n'.join(code_lines)}</pre>")
                code_lines = []
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(html.escape(stripped))
        elif stripped.startswith("# "):
            if in_list:
                paragraphs.append("</ul>")
                in_list = False
            paragraphs.append(f"<h2>{render_inline(stripped[2:])}</h2>")
        elif stripped.startswith("## "):
            if in_list:
                paragraphs.append("</ul>")
                in_list = False
            paragraphs.append(f"<h3>{render_inline(stripped[3:])}</h3>")
        elif stripped.startswith("- "):
            if not in_list:
                paragraphs.append("<ul>")
                in_list = True
            paragraphs.append(f"<li>{render_inline(stripped[2:])}</li>")
        elif stripped:
            if in_list:
                paragraphs.append("</ul>")
                in_list = False
            paragraphs.append(f"<p>{render_inline(stripped)}</p>")
    if in_list:
        paragraphs.append("</ul>")
    if code_lines:
        paragraphs.append(f"<pre>{'\n'.join(code_lines)}</pre>")
    return "\n".join(paragraphs) or "<p class='muted'>Empty page.</p>"


def revision_diff_html(before: WikiRevision | None, after: WikiRevision) -> str:
    before_lines = [] if before is None else before.body.splitlines()
    after_lines = after.body.splitlines()
    rows = difflib.ndiff(before_lines, after_lines)
    html_rows: list[str] = []
    for row in rows:
        prefix = row[:2]
        text = html.escape(row[2:]) or " "
        if prefix == "+ ":
            html_rows.append(f"<tr class='diff-add'><td>+</td><td>{text}</td></tr>")
        elif prefix == "- ":
            html_rows.append(f"<tr class='diff-del'><td>-</td><td>{text}</td></tr>")
        elif prefix == "  ":
            html_rows.append(f"<tr><td></td><td>{text}</td></tr>")
    return "<table class='diff'><tbody>" + "".join(html_rows) + "</tbody></table>"


def flash_message(name: str) -> str:
    messages = {
        "created": "Page created.",
        "saved": "Revision saved.",
        "reverted": "Page reverted.",
    }
    message = messages.get(name)
    return "" if message is None else f"<p class='flash'>{html.escape(message)}</p>"


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
            if path == "/dev/events":
                return Response.json({"events": await wiki.wide_events()})
            if path.startswith("/dev/cached/wiki/"):
                slug = unquote(path.removeprefix("/dev/cached/wiki/"))
                return await cached_wiki_page(wiki, slug)
            if path == "/dev/render" and request.method == "POST":
                data = await form_data(request)
                return html_response(render_markup(data.get("body", "")))
            if path == "/":
                return await show_page(wiki, "home-page")
            if path == "/recent-changes":
                return await recent_page(wiki)
            if path == "/all":
                return await all_pages(wiki)
            if path == "/wanted":
                return await wanted_page(wiki)
            if path == "/search":
                query = parse_qs(parsed.query).get("q", [""])[0]
                return await search_page(wiki, query)
            if path == "/export.jsonl":
                return text_response(await wiki.export_revisions())
            if path.startswith("/wiki/"):
                return await wiki_route(wiki, request, path, parsed.query)
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
        body = shell(
            wiki_title(slug),
            f"<h2>{html.escape(wiki_title(slug))}</h2><p>This page does not exist yet.</p>",
        )
    else:
        body = shell(
            page.title,
            f"<h2>{html.escape(page.title)}</h2><article class='page'>{render_markup(page.body)}</article>",
        )
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
    items = "".join(
        f'<li><a href="/wiki/{quote(page.slug)}">{html.escape(page.title)}</a> '
        f'<span class="muted">r{page.current_revision} · {html.escape(page.updated_at)}</span></li>'
        for page in pages
    )
    body = f"<h2>Recent changes</h2><ul class='page-list'>{items}</ul>"
    return html_response(shell("Recent changes", body))


async def all_pages(wiki: Wiki) -> Response:
    pages = await wiki.all_pages()
    items = "".join(
        f'<li><a href="/wiki/{quote(page.slug)}">{html.escape(page.title)}</a></li>'
        for page in pages
    )
    return html_response(shell("All pages", f"<h2>All pages</h2><ul class='page-list'>{items}</ul>"))


async def wanted_page(wiki: Wiki) -> Response:
    wanted = await wiki.wanted_pages()
    items = "".join(
        f'<li><a class="missing" href="/wiki/{quote(slug)}">{html.escape(wiki_title(slug))}</a> '
        f'<span class="muted">linked {count}×</span></li>'
        for slug, count in wanted
    )
    body = "<h2>Wanted pages</h2>" + (f"<ul>{items}</ul>" if items else "<p>No wanted pages.</p>")
    return html_response(shell("Wanted pages", body))


async def search_page(wiki: Wiki, query: str) -> Response:
    results = await wiki.search(query) if query else []
    items = "".join(
        f'<li><a href="/wiki/{quote(result.slug)}">{html.escape(result.title)}</a>'
        f"<p class='snippet'>{result.snippet}</p></li>"
        for result in results
    )
    body = f"<h2>Search results</h2><p class='muted'>Query: {html.escape(query)}</p>"
    if items:
        body += f"<ul class='search-results'>{items}</ul>"
    elif query:
        slug = slugify(query)
        body += (
            "<p>No results yet. "
            f'<a class="missing" href="/wiki/{quote(slug)}">Create {html.escape(wiki_title(slug))}?</a></p>'
        )
    else:
        body += "<p>Type in the header search box to find pages.</p>"
    return html_response(shell("Search", body, query=query))


async def wiki_route(wiki: Wiki, request: Any, path: str, query: str = "") -> Response:
    rest = path.removeprefix("/wiki/")
    parts = rest.split("/")
    slug = unquote(parts[0])
    validate_slug(slug)
    action = parts[1] if len(parts) > 1 else "show"
    if request.method == "POST" and action == "show":
        data = await form_data(request)
        is_new = await wiki.get_page(slug) is None
        page = await wiki.save_page(
            slug=slug,
            title=data.get("title") or wiki_title(slug),
            body=data.get("body", ""),
            author=data.get("author") or None,
            message=data.get("message") or None,
            base_revision=int(data["base_revision"]) if data.get("base_revision") else None,
        )
        notice = "created" if is_new else "saved"
        return redirect(f"/wiki/{quote(page.slug)}?notice={notice}")
    if request.method == "POST" and action == "revert":
        data = await form_data(request)
        revision = int(data.get("revision", "0"))
        old = await wiki.revision(slug, revision)
        if old is None:
            return html_response(shell("Missing revision", "<p>Revision not found.</p>"), status=404)
        await wiki.save_page(
            slug=slug,
            title=old.title,
            body=old.body,
            author=data.get("author") or "revert",
            message=f"revert to r{revision}",
        )
        return redirect(f"/wiki/{quote(slug)}?notice=reverted")
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
    notice = parse_qs(query).get("notice", [""])[0]
    return await show_page(wiki, slug, notice=notice)


async def backlinks_panel(wiki: Wiki, slug: str) -> str:
    backlinks = await wiki.backlinks(slug)
    if backlinks:
        items = "".join(
            f'<li><a href="/wiki/{quote(page.slug)}">{html.escape(page.title)}</a></li>'
            for page in backlinks
        )
        return f"<aside class='panel'><h3>Backlinks</h3><ul>{items}</ul></aside>"
    return "<aside class='panel'><h3>Backlinks</h3><p class='muted'>No pages link here yet.</p></aside>"


async def show_page(wiki: Wiki, slug: str, *, notice: str = "") -> Response:
    page = await wiki.get_page(slug)
    if page is None:
        return await edit_page(wiki, slug)
    links = (
        f"<p class='page-tools'><a href='/wiki/{quote(slug)}/edit'>Edit</a> · "
        f"<a href='/wiki/{quote(slug)}/history'>History</a> · "
        f"<a href='/wiki/{quote(slug)}/raw'>Raw</a></p>"
    )
    body = (
        f"<main class='wiki-layout'><section>{flash_message(notice)}"
        f"<h2>{html.escape(page.title)}</h2>"
        f"<p class='muted'>Revision {page.current_revision} · {html.escape(page.updated_at)}</p>"
        f"{links}<article class='page'>{render_markup(page.body)}</article>"
        f"</section>{await backlinks_panel(wiki, slug)}</main>"
    )
    return html_response(shell(page.title, body))


async def edit_page(wiki: Wiki, slug: str) -> Response:
    page = await wiki.get_page(slug)
    title = page.title if page else wiki_title(slug)
    body_text = page.body if page else f"# {title}\n\nDescribe [[{title}]] here. Link to [[Home Page]]."
    revision = page.current_revision if page else 0
    guide = """
    <details class="syntax" open><summary>Syntax guide</summary>
      <ul>
        <li><code>[[Page Name]]</code> links to another page and creates it if missing.</li>
        <li><code># Heading</code> and <code>## Subheading</code>.</li>
        <li><code>- item</code> for lists.</li>
        <li><code>```</code> fenced code blocks.</li>
        <li>Traditional WikiWords still link automatically.</li>
      </ul>
    </details>
    """
    verb = "Create page" if page is None else "Save revision"
    form = f"""
    <h2>{verb}: {html.escape(title)}</h2>
    <p class="tabs"><button type="button" data-tab="edit">Edit</button> <button type="button" data-tab="preview">Preview</button> <a href="/wiki/{quote(slug)}">Cancel</a></p>
    <form id="edit-form" method="post" action="/wiki/{quote(slug)}">
      <input type="hidden" name="base_revision" value="{revision}">
      <label>Title <input name="title" value="{html.escape(title)}"></label>
      <section id="edit-tab">
        <label>Body <textarea id="body" name="body">{html.escape(body_text)}</textarea></label>
      </section>
      <section id="preview-tab" hidden><article id="preview" class="page"></article></section>
      <div class="edit-meta">
        <label>Author <input name="author" value="Pythonista"></label>
        <label>Message <input name="message" value="edit {html.escape(title)}"></label>
      </div>
      <p><button>{verb}</button></p>
    </form>
    {guide}
    <script>
    const body = document.querySelector('#body');
    const preview = document.querySelector('#preview');
    async function updatePreview() {{
      const res = await fetch('/dev/render', {{method:'POST', body:new URLSearchParams({{body: body.value}})}});
      preview.innerHTML = await res.text();
    }}
    document.querySelectorAll('[data-tab]').forEach(btn => btn.onclick = async () => {{
      const showPreview = btn.dataset.tab === 'preview';
      document.querySelector('#edit-tab').hidden = showPreview;
      document.querySelector('#preview-tab').hidden = !showPreview;
      if (showPreview) await updatePreview();
    }});
    body.addEventListener('input', () => {{ if (!document.querySelector('#preview-tab').hidden) updatePreview(); }});
    </script>
    """
    return html_response(shell(f"Edit {title}", form))


async def history_page(wiki: Wiki, slug: str) -> Response:
    revisions = await wiki.history(slug)
    blocks: list[str] = []
    previous: WikiRevision | None = None
    for rev in sorted(revisions, key=lambda item: item.revision):
        diff = revision_diff_html(previous, rev)
        blocks.append(
            f"<section class='revision'><h3>r{rev.revision}: {html.escape(rev.title)}</h3>"
            f"<p class='muted'>{html.escape(rev.created_at)} · {html.escape(rev.author or 'unknown')} · {html.escape(rev.message or '')}</p>"
            f"<form method='post' action='/wiki/{quote(slug)}/revert' onsubmit=\"return confirm('Revert to this revision?')\">"
            f"<input type='hidden' name='revision' value='{rev.revision}'><button>Revert to r{rev.revision}</button></form>"
            f"{diff}</section>"
        )
        previous = rev
    body = f"<h2>History for {html.escape(wiki_title(slug))}</h2>{''.join(reversed(blocks))}"
    return html_response(shell(f"History {slug}", body))
