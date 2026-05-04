DROP TABLE IF EXISTS page_search;
DROP TABLE IF EXISTS revisions;
DROP TABLE IF EXISTS pages;

CREATE TABLE pages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  current_revision INTEGER NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE revisions (
  slug TEXT NOT NULL,
  revision INTEGER NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  author TEXT,
  message TEXT,
  created_at TEXT NOT NULL,
  PRIMARY KEY (slug, revision)
);

CREATE VIRTUAL TABLE page_search USING fts5(
  page_id UNINDEXED,
  slug UNINDEXED,
  title,
  body
);

CREATE INDEX idx_pages_updated_at ON pages(updated_at DESC);
CREATE INDEX idx_revisions_slug_revision ON revisions(slug, revision DESC);
