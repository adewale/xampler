DROP TABLE IF EXISTS page_search;
DROP TABLE IF EXISTS page_links;
DROP TABLE IF EXISTS revisions;
DROP TABLE IF EXISTS wide_events;
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

CREATE TABLE page_links (
  from_slug TEXT NOT NULL,
  to_slug TEXT NOT NULL,
  label TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (from_slug, to_slug, label)
);

CREATE VIRTUAL TABLE page_search USING fts5(
  page_id UNINDEXED,
  slug UNINDEXED,
  title,
  body
);

CREATE INDEX idx_pages_updated_at ON pages(updated_at DESC);
CREATE INDEX idx_revisions_slug_revision ON revisions(slug, revision DESC);
CREATE INDEX idx_page_links_to_slug ON page_links(to_slug);

CREATE TABLE wide_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_name TEXT NOT NULL,
  route TEXT NOT NULL,
  method TEXT NOT NULL,
  dimensions TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX idx_wide_events_created_at ON wide_events(created_at DESC);

INSERT INTO pages (slug, title, body, current_revision, updated_at) VALUES
('home-page', 'Home Page', '# Home Page

Welcome to Mini Wiki, a tiny D1-backed wiki for Python Workers.

Start by editing this page, following [[Wiki Guide]], or creating [[Project Ideas]].

## Good wiki loop
- Read a page.
- Follow [[Page Links]].
- Create wanted pages.
- Use backlinks to discover context.', 1, '2026-05-01T00:00:00+00:00'),
('wiki-guide', 'Wiki Guide', '# Wiki Guide

Use [[Page Name]] to link to another page. Missing links become wanted pages.

## Markup
- # Heading
- ## Subheading
- - list item
- ``` fenced code blocks

Search uses D1 FTS and highlights matching snippets.', 1, '2026-05-01T00:01:00+00:00'),
('page-links', 'Page Links', '# Page Links

Links are the heart of the wiki. This page links back to [[Home Page]] and forward to [[Project Ideas]].

Backlinks show every page that points here.', 1, '2026-05-01T00:02:00+00:00');

INSERT INTO revisions (slug, revision, title, body, author, message, created_at)
SELECT slug, current_revision, title, body, 'Seed', 'initial page', updated_at FROM pages;

INSERT INTO page_search (page_id, slug, title, body)
SELECT id, slug, title, body FROM pages;

INSERT INTO page_links (from_slug, to_slug, label, created_at) VALUES
('home-page', 'home-page', 'Home Page', '2026-05-01T00:00:00+00:00'),
('home-page', 'wiki-guide', 'Wiki Guide', '2026-05-01T00:00:00+00:00'),
('home-page', 'project-ideas', 'Project Ideas', '2026-05-01T00:00:00+00:00'),
('home-page', 'page-links', 'Page Links', '2026-05-01T00:00:00+00:00'),
('wiki-guide', 'page-name', 'Page Name', '2026-05-01T00:01:00+00:00'),
('page-links', 'home-page', 'Home Page', '2026-05-01T00:02:00+00:00'),
('page-links', 'project-ideas', 'Project Ideas', '2026-05-01T00:02:00+00:00');
