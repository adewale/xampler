from __future__ import annotations

from dataclasses import dataclass

import pytest

from tests.cloudflare_doubles import PagingKVBinding, SqliteD1Binding
from xampler.d1 import D1Database
from xampler.kv import KVNamespace


async def quotes_db() -> D1Database:
    db = D1Database(SqliteD1Binding())
    await db.execute(
        """
        CREATE TABLE quotes (id INTEGER PRIMARY KEY, quote TEXT NOT NULL, author TEXT);
        CREATE INDEX quotes_author ON quotes(author);
        """
    )
    insert = db.statement("INSERT INTO quotes (quote, author) VALUES (?, ?)")
    await db.batch_run([
        insert.bind("Beautiful is better than ugly", "PEP 20"),
        insert.bind("Now is better than never", "PEP 20"),
        insert.bind("Flat is better than nested", None),
    ])
    return db


@pytest.mark.asyncio
async def test_d1_execute_runs_every_statement() -> None:
    db = await quotes_db()

    objects = await db.query("SELECT type, name FROM sqlite_master ORDER BY name")

    assert objects == [
        {"type": "table", "name": "quotes"},
        {"type": "index", "name": "quotes_author"},
    ]


@pytest.mark.asyncio
async def test_d1_bound_parameters_select_rows() -> None:
    db = await quotes_db()

    assert await db.query("SELECT quote FROM quotes WHERE author = ? ORDER BY id", "PEP 20") == [
        {"quote": "Beautiful is better than ugly"},
        {"quote": "Now is better than never"},
    ]
    assert await db.query_one("SELECT quote FROM quotes WHERE author IS ?", None) == {
        "quote": "Flat is better than nested"
    }
    assert await db.query_one("SELECT quote FROM quotes WHERE author = ?", "nobody") is None
    first_pep = await db.statement("SELECT quote FROM quotes WHERE author = ? ORDER BY id").one(
        "PEP 20"
    )
    assert first_pep == {"quote": "Beautiful is better than ugly"}


@pytest.mark.asyncio
async def test_d1_one_as_builds_typed_rows() -> None:
    @dataclass
    class Quote:
        quote: str
        author: str | None

    db = await quotes_db()
    statement = db.statement("SELECT quote, author FROM quotes WHERE id = ?")

    assert await statement.one_as(Quote, 2) == Quote("Now is better than never", "PEP 20")
    assert await statement.one_as(Quote, 99) is None


@pytest.mark.asyncio
async def test_d1_run_with_params_writes_and_empty_batch_is_a_no_op() -> None:
    db = await quotes_db()

    await db.statement("DELETE FROM quotes WHERE author = ?").run("PEP 20")
    await db.batch_run([])

    assert await db.query("SELECT quote FROM quotes") == [{"quote": "Flat is better than nested"}]


@pytest.mark.asyncio
async def test_d1_batch_is_atomic() -> None:
    db = await quotes_db()
    insert = db.statement("INSERT INTO quotes (quote, author) VALUES (?, ?)")

    with pytest.raises(Exception, match="NOT NULL"):
        await db.batch_run([insert.bind("kept?", "batch"), insert.bind(None, "batch")])

    assert await db.query("SELECT quote FROM quotes WHERE author = ?", "batch") == []


@pytest.mark.asyncio
async def test_kv_json_round_trip_ttl_and_delete() -> None:
    binding = PagingKVBinding()
    key = KVNamespace(binding).key("profile:ada")

    assert await key.read_json() is None
    await key.write_json({"name": "Ada", "langs": ["py"]}, expiration_ttl=60)

    assert await key.read_json() == {"name": "Ada", "langs": ["py"]}
    assert binding.put_options["profile:ada"] == {"expirationTtl": 60}
    await key.delete()
    assert await key.exists() is False


@pytest.mark.asyncio
async def test_kv_list_pages_with_prefix_limit_and_cursor() -> None:
    binding = PagingKVBinding()
    kv = KVNamespace(binding)
    for name in ["notes/b", "notes/a", "notes/c", "images/x"]:
        await kv.key(name).write_text(name)

    first = await kv.list(prefix="notes/", limit=2)
    second = await kv.list(prefix="notes/", limit=2, cursor=first.cursor)

    assert (first.keys, first.complete) == (["notes/a", "notes/b"], False)
    assert (second.keys, second.complete, second.cursor) == (["notes/c"], True, None)


@pytest.mark.asyncio
async def test_kv_iter_keys_follows_cursors_to_the_end() -> None:
    kv = KVNamespace(PagingKVBinding())
    names = [f"user:{i:02}" for i in range(7)]
    for name in [*names, "other"]:
        await kv.key(name).write_text("x")

    seen = [key.name async for key in kv.iter_keys(prefix="user:", page_size=3)]

    assert seen == names
